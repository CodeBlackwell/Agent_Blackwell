"""
Script to run executor integration tests.
"""
import asyncio
import unittest
import inspect
from test_executor_integration import ExecutorIntegrationTest

class AsyncioTestRunner:
    """Helper class to run asyncio tests through unittest."""
    def __init__(self, test_case):
        self.test_case = test_case
    
    def __call__(self):
        """Run the async test using the event loop."""
        # Get the test method name
        test_method = getattr(self.test_case, self.test_case._testMethodName)
        
        # Run the async test method through the event loop
        if inspect.iscoroutinefunction(test_method):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(test_method())
        else:
            test_method()

if __name__ == "__main__":
    print("Running Executor Agent Integration Tests...")
    
    # Patch the ExecutorIntegrationTest to use our runner
    def async_run(self, result=None):
        runner = AsyncioTestRunner(self)
        runner()
        return result
        
    ExecutorIntegrationTest.run = async_run
    
    # Run the tests using standard unittest runner
    unittest.main(module='test_executor_integration', verbosity=2)
