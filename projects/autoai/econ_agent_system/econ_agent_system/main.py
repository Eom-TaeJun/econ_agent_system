#!/usr/bin/env python3
"""
Multi-Agent Economics Analysis System
=====================================
Main entry point for running AI agent-based economic analysis projects.

Agents:
- Perplexity: Research & Search
- Claude: Code Generation
- Gemini: Data Collection
- OpenAI GPT-4: Orchestration

Usage:
    python main.py                      # Interactive mode
    python main.py --query "..."        # Direct query
    python main.py --auto               # Auto mode (no checkpoints)
    python main.py --template variable_discovery
"""

import asyncio
import argparse
import sys
import os
import json
from datetime import datetime
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import API_CONFIG, AGENT_CONFIG
from core.message_bus import MESSAGE_BUS
from agents.openai_orchestrator import create_orchestrator
from workflows.economics_workflow import (
    WorkflowType, get_template, get_all_templates, COMMON_VARIABLES
)
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
# Banner
BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║         🤖 Multi-Agent Economics Analysis System 🤖              ║
╠══════════════════════════════════════════════════════════════════╣
║  Agents:                                                         ║
║    📡 Perplexity  - Research & Web Search                        ║
║    💻 Claude      - Code Generation & Analysis                   ║
║    📊 Gemini      - Data Collection                              ║
║    🎯 OpenAI GPT  - Project Orchestration                        ║
╠══════════════════════════════════════════════════════════════════╣
║  Focus: Economics & Data Analysis | Finding Meaningful Variables ║
╚══════════════════════════════════════════════════════════════════╝
"""

def check_api_keys():
    """Check which API keys are available"""
    print("\n🔑 API Key Status:")
    status = API_CONFIG.validate()
    
    all_present = True
    for api, available in status.items():
        symbol = "✅" if available else "❌"
        print(f"   {symbol} {api.upper()}")
        if not available:
            all_present = False
    
    if not all_present:
        print("\n⚠️  Some API keys are missing!")
        print("   Set them in your environment:")
        print("   export OPENAI_API_KEY='...'")
        print("   export ANTHROPIC_API_KEY='...'")
        print("   export GEMINI_API_KEY='...'")
        print("   export PERPLEXITY_API_KEY='...'")
    
    return status

def show_templates():
    """Display available workflow templates"""
    print("\n📋 Available Workflow Templates:")
    print("-" * 50)
    
    templates = get_all_templates()
    for i, (type_name, template) in enumerate(templates.items(), 1):
        print(f"\n  {i}. {template.name}")
        print(f"     Type: {type_name}")
        print(f"     {template.description}")
    
    print("\n" + "-" * 50)

def show_variables():
    """Display common economic variables"""
    print("\n📊 Common Economic Variables:")
    print("-" * 50)
    
    for category, variables in COMMON_VARIABLES.items():
        print(f"\n  {category.upper()}:")
        print(f"    {', '.join(variables)}")
    
    print("\n" + "-" * 50)

async def run_interactive():
    """Run in interactive mode"""
    print(BANNER)
    check_api_keys()
    
    print("\n💡 Commands:")
    print("   [query]     - Enter your analysis request")
    print("   templates   - Show workflow templates")
    print("   variables   - Show common economic variables")
    print("   auto        - Toggle auto mode (skip checkpoints)")
    print("   quit/exit   - Exit the program")
    print("-" * 50)
    
    orchestrator = create_orchestrator()
    auto_mode = False
    
    while True:
        try:
            user_input = input("\n🎯 Enter query (or command): ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'templates':
                show_templates()
                continue
            
            if user_input.lower() == 'variables':
                show_variables()
                continue
            
            if user_input.lower() == 'auto':
                auto_mode = not auto_mode
                status = "ON" if auto_mode else "OFF"
                print(f"   Auto mode is now {status}")
                continue
            
            # Run the project
            print(f"\n🚀 Starting project analysis...")
            print(f"   Auto mode: {'ON' if auto_mode else 'OFF'}")
            
            result = await orchestrator.run_project(user_input, auto_mode=auto_mode)
            
            # Display results
            print("\n" + "="*60)
            print("📊 PROJECT RESULTS")
            print("="*60)
            
            if 'error' in result:
                print(f"\n❌ Error: {result['error']}")
            else:
                # Show synthesis
                synthesis = result.get('final_output', {}).get('synthesis', '')
                if synthesis:
                    print("\n" + synthesis[:2000])
                    if len(synthesis) > 2000:
                        print("\n... (truncated, see output file for full report)")
                
                # Save results
                output_file = f"outputs/project_{result['task_id']}.json"
                os.makedirs('outputs', exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, default=str, ensure_ascii=False)
                print(f"\n📁 Results saved to: {output_file}")
            
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n\n⏸️  Interrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

async def run_direct(query: str, auto_mode: bool = False, template: str = None):
    """Run with direct query"""
    print(BANNER)
    check_api_keys()
    
    # Apply template if specified
    if template:
        try:
            wf_type = WorkflowType(template)
            wf_template = get_template(wf_type)
            if wf_template:
                query = f"{query}\n\nUse workflow template: {wf_template.name}\n"
                query += f"Research: {wf_template.research_queries}\n"
                query += f"Data: {wf_template.data_requirements}\n"
                query += f"Analysis: {wf_template.analysis_tasks}"
        except ValueError:
            print(f"⚠️  Unknown template: {template}")
    
    orchestrator = create_orchestrator()
    result = await orchestrator.run_project(query, auto_mode=auto_mode)
    
    # Save results
    output_file = f"outputs/project_{result['task_id']}.json"
    os.makedirs('outputs', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"\n📁 Results saved to: {output_file}")
    return result

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Economics Analysis System"
    )
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Direct query to analyze'
    )
    parser.add_argument(
        '--auto', '-a',
        action='store_true',
        help='Run in auto mode (skip user checkpoints)'
    )
    parser.add_argument(
        '--template', '-t',
        type=str,
        choices=[wt.value for wt in WorkflowType],
        help='Use a predefined workflow template'
    )
    parser.add_argument(
        '--list-templates',
        action='store_true',
        help='List available workflow templates'
    )
    
    args = parser.parse_args()
    
    if args.list_templates:
        show_templates()
        return
    
    if args.query:
        asyncio.run(run_direct(args.query, args.auto, args.template))
    else:
        asyncio.run(run_interactive())

if __name__ == "__main__":
    main()
