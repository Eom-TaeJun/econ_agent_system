#!/usr/bin/env python3
"""
Multi-Agent Economics Analysis System (with Report Generation)
==============================================================
Main entry point for running AI agent-based economic analysis projects.

Agents:
- Perplexity: Research & Search
- Claude: Code Generation + Report Writing
- Gemini: Data Collection
- OpenAI GPT-4: Orchestration + Report Summary

Usage:
    python main.py                              # Interactive mode
    python main.py --query "..."                # Direct query
    python main.py --auto                       # Auto mode (no checkpoints)
    python main.py --query "..." --auto --report   # Auto + Report generation
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

# ============================================================================
# Report Generator Integration
# ============================================================================

# Try to import report generator
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'report_generator', 'report_generator'))
    from report_agent import ReportOrchestrator
    REPORT_AVAILABLE = True
except ImportError as e:
    REPORT_AVAILABLE = False
    REPORT_IMPORT_ERROR = str(e)

# Try to import visualization generator
try:
    from visualization_generator import ReportVisualizer
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

# Banner
BANNER = """
╔═══════════════════════════════════════════════════════════════════╗
║         🤖 Multi-Agent Economics Analysis System 🤖               ║
╠═══════════════════════════════════════════════════════════════════╣
║  Agents:                                                          ║
║    📡 Perplexity  - Research & Web Search                         ║
║    💻 Claude      - Code Generation & Analysis                    ║
║    📊 Gemini      - Data Collection                               ║
║    🎯 OpenAI GPT  - Project Orchestration                         ║
╠═══════════════════════════════════════════════════════════════════╣
║  Focus: Economics & Data Analysis | Finding Meaningful Variables  ║
╠═══════════════════════════════════════════════════════════════════╣
║  📄 Report Generation: {report_status}                                       ║
╚═══════════════════════════════════════════════════════════════════╝
"""

def get_banner():
    """Get banner with report status"""
    status = "✅ Available" if REPORT_AVAILABLE else "❌ Unavailable"
    return BANNER.format(report_status=status.ljust(12))

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


# ============================================================================
# Report Generation Functions
# ============================================================================

async def generate_report_from_json(json_path: str, output_name: str = None,
                                     korean_only: bool = False,
                                     english_only: bool = False,
                                     include_visuals: bool = True):
    """Generate DOCX report from analysis JSON output with visualizations"""
    
    if not REPORT_AVAILABLE:
        print(f"❌ Report Generator not available: {REPORT_IMPORT_ERROR}")
        print("   Install with: pip install anthropic openai")
        return None
    
    print("\n" + "="*60)
    print("📊 GENERATING BILINGUAL REPORT WITH VISUALIZATIONS")
    print("="*60)
    print("   🤖 Claude  → Methodology, Results, Discussion")
    print("   🤖 GPT-4   → Executive Summary, Introduction, Conclusion")
    print("   📊 Charts  → Heatmap, Time Series, Tables")
    print("="*60)
    
    try:
        # Get task_id first
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        task_id = json_data.get('task_id', 'unknown')
        
        # 1. Generate visualizations (if available)
        visuals_file = None
        if include_visuals and VISUALIZATION_AVAILABLE:
            print("\n📊 Generating visualizations...")
            try:
                visualizer = ReportVisualizer(output_dir='outputs/report_images')
                visuals_result = visualizer.generate_from_json(json_path)
                
                if visuals_result.images or visuals_result.tables:
                    visuals_file = f"outputs/visualization_result_{task_id}.json"
                    with open(visuals_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'images': visuals_result.images,
                            'tables': visuals_result.tables,
                            'metadata': visuals_result.metadata
                        }, f, indent=2, ensure_ascii=False)
                    print(f"   📁 Visuals saved: {visuals_file}")
            except Exception as e:
                print(f"   ⚠️ Visualization failed: {e}")
        elif include_visuals and not VISUALIZATION_AVAILABLE:
            print("   ⚠️ Visualization not available (install matplotlib, seaborn)")
        
        # 2. Generate text sections
        orchestrator = ReportOrchestrator()
        result = await orchestrator.generate_report(json_path)
        
        # Save sections
        sections_file = f"outputs/report_sections_{task_id}.json"
        
        with open(sections_file, 'w', encoding='utf-8') as f:
            json.dump({
                'sections': result['sections'],
                'metadata': result['metadata']
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📁 Sections saved: {sections_file}")
        
        # 3. Build DOCX using Node.js
        output_name = output_name or f"outputs/report_{task_id}"
        docx_path = await build_docx(sections_file, output_name, visuals_file)
        
        if docx_path:
            print(f"\n✅ Report generated successfully!")
            print(f"   📄 DOCX: {docx_path}")
            return docx_path
        
    except Exception as e:
        print(f"\n❌ Report generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def build_docx(sections_file: str, output_name: str, visuals_file: str = None):
    """Build DOCX using Node.js document_builder.js (with optional visuals)"""
    import subprocess
    
    script_dir = os.path.join(os.path.dirname(__file__), 'report_generator', 'report_generator')
    
    # Prefer v2 builder (supports images/tables), fallback to original
    builder_path = os.path.join(script_dir, 'document_builder_v2.js')
    if not os.path.exists(builder_path):
        builder_path = os.path.join(script_dir, 'document_builder.js')
    
    if not os.path.exists(builder_path):
        print(f"   ⚠️ document_builder.js not found at {script_dir}")
        return None
    
    print(f"\n🔨 Building DOCX document...")
    
    # Check if docx is installed
    try:
        check = subprocess.run(
            ['node', '-e', "require('docx')"],
            capture_output=True,
            cwd=script_dir
        )
        if check.returncode != 0:
            print("   📦 Installing docx package...")
            subprocess.run(['npm', 'install', 'docx'], cwd=script_dir, check=True)
    except Exception as e:
        print(f"   ⚠️ Node.js check failed: {e}")
    
    # Build command with absolute paths
    sections_abs = os.path.abspath(sections_file)
    output_abs = os.path.abspath(output_name)
    
    cmd = ['node', builder_path, sections_abs, output_abs]
    
    # Add visuals if available
    if visuals_file and os.path.exists(visuals_file):
        visuals_abs = os.path.abspath(visuals_file)
        cmd.extend(['--visuals', visuals_abs])
        print(f"   📊 Including visualizations from: {visuals_file}")
    
    # Run document builder
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=script_dir
    )
    
    if result.returncode != 0:
        print(f"   ❌ DOCX build failed: {result.stderr}")
        return None
    
    print(result.stdout)
    return f"{output_abs}.docx"


# ============================================================================
# Main Workflow Functions
# ============================================================================

async def run_interactive():
    """Run in interactive mode"""
    print(get_banner())
    check_api_keys()
    
    print("\n💡 Commands:")
    print("   [query]     - Enter your analysis request")
    print("   templates   - Show workflow templates")
    print("   variables   - Show common economic variables")
    print("   auto        - Toggle auto mode (skip checkpoints)")
    print("   report      - Toggle report generation")
    print("   quit/exit   - Exit the program")
    print("-" * 50)
    
    orchestrator = create_orchestrator()
    auto_mode = False
    report_mode = False
    
    while True:
        try:
            mode_status = []
            if auto_mode:
                mode_status.append("AUTO")
            if report_mode:
                mode_status.append("REPORT")
            mode_str = f" [{', '.join(mode_status)}]" if mode_status else ""
            
            user_input = input(f"\n🎯 Enter query{mode_str}: ").strip()
            
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
            
            if user_input.lower() == 'report':
                if not REPORT_AVAILABLE:
                    print(f"   ❌ Report Generator not available")
                    continue
                report_mode = not report_mode
                status = "ON" if report_mode else "OFF"
                print(f"   Report generation is now {status}")
                continue
            
            # Run the project
            print(f"\n🚀 Starting project analysis...")
            print(f"   Auto mode: {'ON' if auto_mode else 'OFF'}")
            print(f"   Report mode: {'ON' if report_mode else 'OFF'}")
            
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
                
                # Generate report if enabled
                if report_mode and REPORT_AVAILABLE:
                    await generate_report_from_json(output_file)
            
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n\n⏸️  Interrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


async def run_direct(query: str, auto_mode: bool = False, template: str = None,
                     generate_report: bool = False, korean_only: bool = False,
                     english_only: bool = False):
    """Run with direct query"""
    print(get_banner())
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
    
    # Generate report if requested
    if generate_report:
        if REPORT_AVAILABLE:
            await generate_report_from_json(
                output_file,
                korean_only=korean_only,
                english_only=english_only
            )
        else:
            print(f"\n⚠️ Report generation skipped: {REPORT_IMPORT_ERROR}")
    
    return result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Economics Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                                    # Interactive mode
    python main.py -q "Analyze Bitcoin" -a            # Direct query, auto mode
    python main.py -q "Analyze Bitcoin" -a -r         # With report generation
    python main.py -q "Analyze Bitcoin" -a -r -k      # Korean-only report
        """
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
    # Report generation arguments
    parser.add_argument(
        '--report', '-r',
        action='store_true',
        help='Generate DOCX report after analysis'
    )
    parser.add_argument(
        '--korean-only', '-k',
        action='store_true',
        help='Generate Korean-only report'
    )
    parser.add_argument(
        '--english-only', '-e',
        action='store_true',
        help='Generate English-only report'
    )
    
    args = parser.parse_args()
    
    if args.list_templates:
        show_templates()
        return
    
    if args.query:
        asyncio.run(run_direct(
            args.query,
            args.auto,
            args.template,
            generate_report=args.report,
            korean_only=args.korean_only,
            english_only=args.english_only
        ))
    else:
        asyncio.run(run_interactive())


if __name__ == "__main__":
    main()
