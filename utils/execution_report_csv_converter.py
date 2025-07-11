"""
Execution Report CSV Converter

Converts JSON execution reports to CSV format for better data compression and analysis.
"""

import json
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class ExecutionReportCSVConverter:
    """Converts execution report JSON to CSV format"""
    
    def __init__(self):
        self.csv_data = {
            'summary': [],
            'agent_exchanges': [],
            'events': [],
            'files': [],
            'errors': []
        }
    
    def convert_json_to_csv(self, json_path: str, output_dir: str = None) -> Dict[str, str]:
        """
        Convert JSON execution report to multiple CSV files
        
        Args:
            json_path: Path to the JSON execution report
            output_dir: Output directory for CSV files (defaults to same dir as JSON)
            
        Returns:
            Dictionary mapping CSV type to file path
        """
        # Load JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Set output directory
        if output_dir is None:
            output_dir = os.path.dirname(json_path)
        
        # Extract session ID for file naming
        session_id = data.get('session_id', 'unknown')
        
        # Convert different sections
        self._extract_summary(data, session_id)
        self._extract_agent_exchanges(data.get('agent_exchanges', []), session_id)
        self._extract_events(data.get('events', []), session_id)
        self._extract_files(data, session_id)
        self._extract_errors(data, session_id)
        
        # Write CSV files
        output_files = {}
        
        # Write summary CSV
        summary_path = os.path.join(output_dir, f'execution_summary_{session_id}.csv')
        self._write_summary_csv(summary_path)
        output_files['summary'] = summary_path
        
        # Write agent exchanges CSV
        exchanges_path = os.path.join(output_dir, f'agent_exchanges_{session_id}.csv')
        self._write_exchanges_csv(exchanges_path)
        output_files['exchanges'] = exchanges_path
        
        # Write events CSV if available
        if self.csv_data['events']:
            events_path = os.path.join(output_dir, f'events_{session_id}.csv')
            self._write_events_csv(events_path)
            output_files['events'] = events_path
        
        # Write files CSV if available
        if self.csv_data['files']:
            files_path = os.path.join(output_dir, f'files_{session_id}.csv')
            self._write_files_csv(files_path)
            output_files['files'] = files_path
        
        # Write errors CSV if available
        if self.csv_data['errors']:
            errors_path = os.path.join(output_dir, f'errors_{session_id}.csv')
            self._write_errors_csv(errors_path)
            output_files['errors'] = errors_path
        
        # Create a combined report
        combined_path = os.path.join(output_dir, f'execution_report_{session_id}.csv')
        self._write_combined_csv(combined_path, data)
        output_files['combined'] = combined_path
        
        return output_files
    
    def _extract_summary(self, data: Dict[str, Any], session_id: str):
        """Extract summary information"""
        summary = {
            'session_id': session_id,
            'start_time': data.get('start_time', ''),
            'end_time': data.get('end_time', ''),
            'duration_ms': data.get('duration_ms', 0),
            'workflow_type': data.get('original_command', {}).get('config_type', ''),
            'requirements': data.get('original_command', {}).get('requirements', ''),
            'total_events': data.get('metrics', {}).get('total_events', 0),
            'agent_interactions': data.get('metrics', {}).get('agent_interactions', 0),
            'commands_executed': data.get('metrics', {}).get('commands_executed', 0),
            'tests_run': data.get('metrics', {}).get('tests_run', 0),
            'files_created': data.get('metrics', {}).get('files_created', 0),
            'files_modified': data.get('metrics', {}).get('files_modified', 0),
            'success': data.get('success', True),
            'error': data.get('error', '')
        }
        self.csv_data['summary'].append(summary)
    
    def _extract_agent_exchanges(self, exchanges: List[Dict], session_id: str):
        """Extract agent exchange information"""
        for exchange in exchanges:
            row = {
                'session_id': session_id,
                'agent_name': exchange.get('agent_name', ''),
                'phase': exchange.get('phase', ''),
                'iteration': exchange.get('iteration', 0),
                'request_time': exchange.get('request_time', ''),
                'response_time': exchange.get('response_time', ''),
                'duration_ms': exchange.get('duration_ms', 0),
                'success': exchange.get('success', True),
                'error': exchange.get('error', ''),
                'request_task': exchange.get('request_data', {}).get('task', ''),
                'request_phase': exchange.get('request_data', {}).get('phase', ''),
                'response_type': exchange.get('response_data', {}).get('type', ''),
                'files_count': len(exchange.get('response_data', {}).get('files', [])),
                'streaming_chunks': exchange.get('streaming_chunks_count', 0)
            }
            self.csv_data['agent_exchanges'].append(row)
    
    def _extract_events(self, events: List[Dict], session_id: str):
        """Extract event information"""
        for event in events:
            row = {
                'session_id': session_id,
                'timestamp': event.get('timestamp', ''),
                'event_type': event.get('event_type', ''),
                'phase': event.get('phase', ''),
                'agent': event.get('agent', ''),
                'description': event.get('description', ''),
                'data': json.dumps(event.get('data', {}))[:500]  # Truncate long data
            }
            self.csv_data['events'].append(row)
    
    def _extract_files(self, data: Dict, session_id: str):
        """Extract file information from agent exchanges"""
        for exchange in data.get('agent_exchanges', []):
            if exchange.get('agent_name') == 'coder':
                files = exchange.get('response_data', {}).get('files', [])
                existing_files = exchange.get('request_data', {}).get('existing_files', {})
                
                # Track new files
                for file_path in files:
                    self.csv_data['files'].append({
                        'session_id': session_id,
                        'file_path': file_path,
                        'operation': 'created',
                        'agent': exchange.get('agent_name', ''),
                        'phase': exchange.get('phase', ''),
                        'timestamp': exchange.get('response_time', '')
                    })
                
                # Track existing files
                for file_path in existing_files.keys():
                    self.csv_data['files'].append({
                        'session_id': session_id,
                        'file_path': file_path,
                        'operation': 'exists',
                        'agent': exchange.get('agent_name', ''),
                        'phase': exchange.get('phase', ''),
                        'timestamp': exchange.get('request_time', '')
                    })
    
    def _extract_errors(self, data: Dict, session_id: str):
        """Extract error information"""
        # Check main error
        if data.get('error'):
            self.csv_data['errors'].append({
                'session_id': session_id,
                'timestamp': data.get('end_time', ''),
                'error_type': 'workflow_error',
                'agent': '',
                'phase': '',
                'error_message': data.get('error', ''),
                'details': ''
            })
        
        # Check agent errors
        for exchange in data.get('agent_exchanges', []):
            if exchange.get('error'):
                self.csv_data['errors'].append({
                    'session_id': session_id,
                    'timestamp': exchange.get('response_time', ''),
                    'error_type': 'agent_error',
                    'agent': exchange.get('agent_name', ''),
                    'phase': exchange.get('phase', ''),
                    'error_message': exchange.get('error', ''),
                    'details': json.dumps(exchange.get('request_data', {}))[:200]
                })
    
    def _write_summary_csv(self, path: str):
        """Write summary CSV"""
        if not self.csv_data['summary']:
            return
        
        with open(path, 'w', newline='') as f:
            if self.csv_data['summary']:
                writer = csv.DictWriter(f, fieldnames=self.csv_data['summary'][0].keys())
                writer.writeheader()
                writer.writerows(self.csv_data['summary'])
    
    def _write_exchanges_csv(self, path: str):
        """Write agent exchanges CSV"""
        if not self.csv_data['agent_exchanges']:
            return
        
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_data['agent_exchanges'][0].keys())
            writer.writeheader()
            writer.writerows(self.csv_data['agent_exchanges'])
    
    def _write_events_csv(self, path: str):
        """Write events CSV"""
        if not self.csv_data['events']:
            return
        
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_data['events'][0].keys())
            writer.writeheader()
            writer.writerows(self.csv_data['events'])
    
    def _write_files_csv(self, path: str):
        """Write files CSV"""
        if not self.csv_data['files']:
            return
        
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_data['files'][0].keys())
            writer.writeheader()
            writer.writerows(self.csv_data['files'])
    
    def _write_errors_csv(self, path: str):
        """Write errors CSV"""
        if not self.csv_data['errors']:
            return
        
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_data['errors'][0].keys())
            writer.writeheader()
            writer.writerows(self.csv_data['errors'])
    
    def _write_combined_csv(self, path: str, data: Dict):
        """Write a combined CSV with key metrics in a single file"""
        rows = []
        
        # Add header row with session info
        session_id = data.get('session_id', 'unknown')
        
        # For each agent exchange, create a row
        for idx, exchange in enumerate(data.get('agent_exchanges', [])):
            row = {
                'session_id': session_id,
                'sequence': idx + 1,
                'timestamp': exchange.get('request_time', ''),
                'agent': exchange.get('agent_name', ''),
                'phase': exchange.get('phase', ''),
                'iteration': exchange.get('iteration', 0),
                'duration_ms': exchange.get('duration_ms', 0),
                'success': exchange.get('success', True),
                'error': exchange.get('error', ''),
                'task': exchange.get('request_data', {}).get('task', ''),
                'files_created': len(exchange.get('response_data', {}).get('files', [])),
                'response_type': exchange.get('response_data', {}).get('type', '')
            }
            rows.append(row)
        
        # Write to CSV
        if rows:
            # Add summary metrics to first row
            rows[0]['total_duration_ms'] = data.get('duration_ms', 0)
            rows[0]['total_agents'] = data.get('metrics', {}).get('agent_interactions', 0)
            rows[0]['total_files'] = data.get('metrics', {}).get('files_created', 0)
            rows[0]['workflow_success'] = data.get('success', True)
            
            # Get all fieldnames (including the summary fields)
            fieldnames = list(rows[0].keys())
            
            with open(path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)


def convert_execution_report(json_path: str, output_dir: str = None) -> Dict[str, str]:
    """
    Convenience function to convert execution report
    
    Args:
        json_path: Path to JSON execution report
        output_dir: Output directory (optional)
        
    Returns:
        Dictionary of output file paths
    """
    converter = ExecutionReportCSVConverter()
    return converter.convert_json_to_csv(json_path, output_dir)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python execution_report_csv_converter.py <json_report_path> [output_dir]")
        sys.exit(1)
    
    json_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        output_files = convert_execution_report(json_path, output_dir)
        print("CSV files created:")
        for csv_type, file_path in output_files.items():
            print(f"  {csv_type}: {file_path}")
    except Exception as e:
        print(f"Error converting report: {e}")
        sys.exit(1)