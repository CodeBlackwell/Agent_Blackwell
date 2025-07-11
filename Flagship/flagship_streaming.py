"""
Streaming handler for Flagship TDD Orchestrator

Provides real-time streaming of agent outputs without stdout redirection issues.
"""

import asyncio
from typing import AsyncGenerator, Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import json


@dataclass
class StreamChunk:
    """A single chunk of streamed data."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    text: str = ""
    type: str = "output"  # output, status, error
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Convert to JSON string for streaming."""
        return json.dumps({
            "timestamp": self.timestamp,
            "text": self.text,
            "type": self.type,
            "metadata": self.metadata
        })


class StreamBuffer:
    """Thread-safe buffer for collecting stream chunks."""
    
    def __init__(self):
        self._chunks: List[StreamChunk] = []
        self._lock = asyncio.Lock()
        self._new_chunks_event = asyncio.Event()
        self._position = 0
        
    async def add_chunk(self, chunk: StreamChunk):
        """Add a chunk to the buffer."""
        async with self._lock:
            self._chunks.append(chunk)
            self._new_chunks_event.set()
            
    async def add_text(self, text: str, type: str = "output"):
        """Add text as a chunk."""
        chunk = StreamChunk(text=text, type=type)
        await self.add_chunk(chunk)
        
    async def get_chunks_from(self, position: int) -> List[StreamChunk]:
        """Get all chunks starting from a position."""
        async with self._lock:
            return self._chunks[position:]
            
    async def wait_for_new_chunks(self):
        """Wait for new chunks to be added."""
        await self._new_chunks_event.wait()
        self._new_chunks_event.clear()
        
    def get_all_text(self) -> str:
        """Get all text from all chunks."""
        return "".join(chunk.text for chunk in self._chunks)


class StreamingOrchestrator:
    """Wrapper for FlagshipOrchestrator that captures streaming output."""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.buffer = StreamBuffer()
        
    async def run_tdd_workflow(self, requirements: str):
        """Run TDD workflow with streaming capture."""
        # Patch the orchestrator's agent methods to capture streaming
        original_run_red = self.orchestrator._run_red_phase
        original_run_yellow = self.orchestrator._run_yellow_phase
        original_run_green = self.orchestrator._run_green_phase
        
        async def streaming_red_phase():
            await self.buffer.add_text(f"\n🔴 Entering RED Phase: Writing failing tests...\n", "phase")
            
            # Capture test writer output
            test_code = ""
            exchange_id = self.orchestrator.tracer.start_agent_exchange(
                "TestWriterFlagship", "RED", 
                self.orchestrator.state.iteration_count,
                {"requirements": self.orchestrator.state.requirements}
            )
            
            async for chunk in self.orchestrator.test_writer.write_tests(
                self.orchestrator.state.requirements
            ):
                await self.buffer.add_text(chunk)
                test_code += chunk
                self.orchestrator.tracer.add_streaming_chunk(exchange_id, chunk)
            
            # Continue with original logic
            self.orchestrator.test_writer._test_code = test_code
            
            if test_code:
                self.orchestrator.state.generated_tests.append(test_code)
                self.orchestrator.tracer.trace_file_operation("create", "test_generated.py", len(test_code))
                
            self.orchestrator.tracer.complete_agent_exchange(
                exchange_id,
                {"test_code_generated": bool(test_code), "test_code_length": len(test_code)}
            )
            
            self.orchestrator.tracer.trace_event(
                EventType.PHASE_END,
                phase="RED",
                iteration=self.orchestrator.state.iteration_count,
                data={"success": bool(test_code)}
            )
            
            return bool(test_code)
            
        async def streaming_yellow_phase():
            await self.buffer.add_text(f"\n🟡 Entering YELLOW Phase: Writing minimal implementation...\n", "phase")
            
            # Get test results
            test_code = self.orchestrator.state.generated_tests[-1] if self.orchestrator.state.generated_tests else ""
            
            # Get test results from last GREEN phase (if any)
            last_green = self.orchestrator.state.get_latest_phase_result(TDDPhase.GREEN)
            test_results = last_green.test_results if last_green else []
            
            # If no test results yet, create "NOT_RUN" results
            if not test_results:
                # Create NOT_RUN results for all tests
                test_results = []
                for line in test_code.split('\n'):
                    if line.strip().startswith('def test_'):
                        test_name = line.strip().split('(')[0].replace('def ', '')
                        test_results.append(TestResult(
                            test_name=test_name,
                            status=TestStatus.NOT_RUN,
                            error_message="Test not yet executed"
                        ))
            
            exchange_id = self.orchestrator.tracer.start_agent_exchange(
                "CoderFlagship", "YELLOW",
                self.orchestrator.state.iteration_count,
                {"test_code": test_code[:500], "test_results_count": len(test_results)}
            )
            
            # Capture coder output
            implementation_code = ""
            async for chunk in self.orchestrator.coder.write_code(test_code, test_results):
                await self.buffer.add_text(chunk)
                implementation_code += chunk
                self.orchestrator.tracer.add_streaming_chunk(exchange_id, chunk)
            
            # Continue with original logic
            self.orchestrator.coder._implementation_code = implementation_code
            
            if implementation_code:
                self.orchestrator.state.generated_code.append(implementation_code)
                self.orchestrator.tracer.trace_file_operation("create", "implementation_generated.py", len(implementation_code))
                
            self.orchestrator.tracer.complete_agent_exchange(
                exchange_id,
                {"implementation_generated": bool(implementation_code), "implementation_length": len(implementation_code)}
            )
            
            self.orchestrator.tracer.trace_event(
                EventType.PHASE_END,
                phase="YELLOW",
                iteration=self.orchestrator.state.iteration_count,
                data={"success": bool(implementation_code)}
            )
            
            return bool(implementation_code)
            
        async def streaming_green_phase():
            await self.buffer.add_text(f"\n🟢 Entering GREEN Phase: Running tests...\n", "phase")
            
            # Get current test and implementation
            test_code = self.orchestrator.state.generated_tests[-1] if self.orchestrator.state.generated_tests else ""
            impl_code = self.orchestrator.state.generated_code[-1] if self.orchestrator.state.generated_code else ""
            
            exchange_id = self.orchestrator.tracer.start_agent_exchange(
                "TestRunnerFlagship", "GREEN",
                self.orchestrator.state.iteration_count,
                {"test_code_length": len(test_code), "implementation_length": len(impl_code)}
            )
            
            # Capture test runner output
            async for chunk in self.orchestrator.test_runner.run_tests(test_code, impl_code):
                await self.buffer.add_text(chunk)
                self.orchestrator.tracer.add_streaming_chunk(exchange_id, chunk)
            
            # Get test results
            test_results = self.orchestrator.test_runner.get_test_results()
            all_passed = all(tr.status == TestStatus.PASSED for tr in test_results)
            
            # Create phase result and store it
            result = self.orchestrator.test_runner.create_phase_result()
            self.orchestrator.state.add_phase_result(result)
            
            # Trace test execution
            test_duration = (datetime.now() - datetime.fromisoformat(
                self.orchestrator.tracer.current_exchanges[exchange_id].request_time
            )).total_seconds() * 1000
            
            test_results_data = [
                {
                    "test_name": tr.test_name,
                    "status": tr.status.value,
                    "error_message": tr.error_message
                }
                for tr in test_results
            ]
            self.orchestrator.tracer.trace_test_execution(
                "test_generated.py",
                test_results_data,
                test_duration
            )
            
            self.orchestrator.tracer.complete_agent_exchange(
                exchange_id,
                response_data={
                    "all_tests_passed": all_passed,
                    "test_count": len(test_results),
                    "passed_count": sum(1 for t in test_results if t.status == TestStatus.PASSED),
                    "failed_count": sum(1 for t in test_results if t.status != TestStatus.PASSED)
                }
            )
            
            self.orchestrator.tracer.trace_event(
                EventType.PHASE_END,
                phase="GREEN",
                iteration=self.orchestrator.state.iteration_count,
                data={"success": all_passed, "test_results": len(test_results)}
            )
            
            self.orchestrator.state.all_tests_passing = all_passed
            
            if all_passed:
                await self.buffer.add_text("✅ All tests passing! TDD cycle complete.\n", "success")
            else:
                failed_count = sum(1 for t in test_results if t.status != TestStatus.PASSED)
                await self.buffer.add_text(f"⚠️  Some tests still failing. Starting next iteration...\n", "warning")
            
            return all_passed
        
        # Replace methods
        self.orchestrator._run_red_phase = streaming_red_phase
        self.orchestrator._run_yellow_phase = streaming_yellow_phase
        self.orchestrator._run_green_phase = streaming_green_phase
        
        # Run the workflow
        result = await self.orchestrator.run_tdd_workflow(requirements)
        
        # Restore original methods
        self.orchestrator._run_red_phase = original_run_red
        self.orchestrator._run_yellow_phase = original_run_yellow
        self.orchestrator._run_green_phase = original_run_green
        
        return result


async def create_streaming_generator(buffer: StreamBuffer, 
                                   session_id: str,
                                   workflows: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """Create an async generator for streaming chunks."""
    position = 0
    
    while True:
        # Get workflow status
        workflow = workflows.get(session_id)
        if not workflow:
            break
            
        # Get new chunks
        chunks = await buffer.get_chunks_from(position)
        
        if chunks:
            # Send new chunks
            for chunk in chunks:
                yield chunk.to_json() + "\n"
            position += len(chunks)
            
        # Check if workflow is complete
        if workflow["status"] != "running":
            # Send final status
            yield json.dumps({
                "type": "status",
                "status": workflow["status"],
                "results": workflow.get("results")
            }) + "\n"
            break
            
        # Wait for new chunks or timeout
        try:
            await asyncio.wait_for(buffer.wait_for_new_chunks(), timeout=1.0)
        except asyncio.TimeoutError:
            # Send heartbeat
            yield json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            }) + "\n"


# Import the required types
from models.flagship_models import TestStatus, TDDPhase, TestResult, PhaseResult
from models.execution_tracer import EventType