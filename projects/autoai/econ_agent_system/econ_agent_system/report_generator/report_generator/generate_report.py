#!/usr/bin/env python3
"""
Report Generator CLI
====================
One-command report generation from Multi-Agent System JSON outputs.

Usage:
    python generate_report.py <json_file> [options]

Examples:
    python generate_report.py outputs/project_45ffab5c.json
    python generate_report.py project.json --output my_report
    python generate_report.py project.json --korean-only
    python generate_report.py project.json --english-only
"""

import asyncio
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_agent import ReportOrchestrator, JSONReportParser


def check_dependencies():
    """Check if required dependencies are installed"""
    issues = []
    
    # Check Python packages
    try:
        import anthropic
    except ImportError:
        issues.append("anthropic (pip install anthropic)")
    
    try:
        import openai
    except ImportError:
        issues.append("openai (pip install openai)")
    
    # Check Node.js and docx
    try:
        result = subprocess.run(['node', '-v'], capture_output=True, text=True)
        if result.returncode != 0:
            issues.append("Node.js")
    except FileNotFoundError:
        issues.append("Node.js")
    
    # Check API keys
    if not os.getenv('ANTHROPIC_API_KEY'):
        issues.append("ANTHROPIC_API_KEY environment variable")
    if not os.getenv('OPENAI_API_KEY'):
        issues.append("OPENAI_API_KEY environment variable")
    
    return issues


def preview_json(json_path: str):
    """Preview JSON file structure"""
    parser = JSONReportParser()
    report = parser.parse(json_path)
    
    print("\n" + "="*60)
    print("📄 JSON Preview")
    print("="*60)
    print(f"\n📌 Task ID: {report.task_id}")
    print(f"📌 Title: {report.plan.title}")
    print(f"📌 Objective: {report.plan.objective[:100]}...")
    print(f"\n📊 Phases: {len(report.phase_results)}")
    for phase in report.phase_results:
        print(f"   • Phase {phase.phase_number}: {phase.name} ({phase.agent})")
    print(f"\n📝 Synthesis length: {len(report.synthesis)} chars")
    print("="*60)
    
    return report


async def generate_sections(json_path: str, language: str = 'both') -> dict:
    """Generate report sections using AI agents"""
    orchestrator = ReportOrchestrator()
    
    if language == 'korean':
        print("\n🇰🇷 Generating Korean-only report...")
    elif language == 'english':
        print("\n🇺🇸 Generating English-only report...")
    else:
        print("\n🌐 Generating bilingual report (Korean + English)...")
    
    result = await orchestrator.generate_report(json_path)
    return result


def build_document(sections_path: str, output_name: str):
    """Build DOCX document using Node.js"""
    print(f"\n🔨 Building DOCX document...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    builder_path = os.path.join(script_dir, 'document_builder.js')
    
    # ✅ 절대 경로로 변환
    sections_abs_path = os.path.abspath(sections_path)
    output_abs_path = os.path.abspath(output_name)
    
    print(f"   📂 Sections: {sections_abs_path}")
    print(f"   📂 Output: {output_abs_path}")
    
    # Check if sections file exists
    if not os.path.exists(sections_abs_path):
        print(f"   ❌ Error: Sections file not found: {sections_abs_path}")
        return None
    
    # Install docx if needed
    try:
        result = subprocess.run(
            ['node', '-e', "require('docx')"],
            capture_output=True,
            cwd=script_dir
        )
        if result.returncode != 0:
            print("   📦 Installing docx package...")
            subprocess.run(['npm', 'install', 'docx'], cwd=script_dir, check=True)
    except Exception as e:
        print(f"   ⚠️ Warning: {e}")
    
    # ✅ 절대 경로로 document_builder.js 실행
    result = subprocess.run(
        ['node', builder_path, sections_abs_path, output_abs_path],
        capture_output=True,
        text=True,
        cwd=script_dir
    )
    
    if result.returncode != 0:
        print(f"   ❌ Error: {result.stderr}")
        return None
    
    print(result.stdout)
    return f"{output_abs_path}.docx"


async def main():
    parser = argparse.ArgumentParser(
        description="Generate professional reports from Multi-Agent System JSON outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python generate_report.py project.json
    python generate_report.py project.json --output analysis_report
    python generate_report.py project.json --preview
        """
    )
    
    parser.add_argument('json_file', help='Path to JSON file from Multi-Agent System')
    parser.add_argument('--output', '-o', default=None, help='Output filename (without extension)')
    parser.add_argument('--preview', '-p', action='store_true', help='Preview JSON structure only')
    parser.add_argument('--korean-only', '-k', action='store_true', help='Generate Korean-only report')
    parser.add_argument('--english-only', '-e', action='store_true', help='Generate English-only report')
    parser.add_argument('--skip-docx', action='store_true', help='Generate sections only (skip DOCX)')
    parser.add_argument('--check', '-c', action='store_true', help='Check dependencies')
    
    args = parser.parse_args()
    
    # Dependency check
    if args.check:
        issues = check_dependencies()
        if issues:
            print("❌ Missing dependencies:")
            for issue in issues:
                print(f"   • {issue}")
            sys.exit(1)
        else:
            print("✅ All dependencies are available!")
            sys.exit(0)
    
    # Validate input file
    json_abs_path = os.path.abspath(args.json_file)
    if not os.path.exists(json_abs_path):
        print(f"❌ Error: File not found: {json_abs_path}")
        sys.exit(1)
    
    # Banner
    print("""
╔══════════════════════════════════════════════════════════════╗
║           📊 Multi-Agent Report Generator 📊                  ║
╠══════════════════════════════════════════════════════════════╣
║  Claude (Anthropic) → Detailed Analysis                      ║
║  GPT-4 (OpenAI)     → Summary & Structure                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Preview mode
    if args.preview:
        preview_json(json_abs_path)
        return
    
    # Check dependencies
    issues = check_dependencies()
    if issues:
        print("❌ Missing dependencies:")
        for issue in issues:
            print(f"   • {issue}")
        print("\nRun with --check for more details")
        sys.exit(1)
    
    # Determine language
    language = 'both'
    if args.korean_only:
        language = 'korean'
    elif args.english_only:
        language = 'english'
    
    # Generate sections
    result = await generate_sections(json_abs_path, language)
    
    # ✅ Save sections - 현재 작업 디렉토리 기준 절대 경로
    task_id = result['metadata']['task_id']
    current_dir = os.getcwd()
    sections_file = os.path.join(current_dir, f"report_sections_{task_id}.json")
    
    with open(sections_file, 'w', encoding='utf-8') as f:
        json.dump({
            'sections': result['sections'],
            'metadata': result['metadata']
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 Sections saved: {sections_file}")
    
    # Build DOCX
    if not args.skip_docx:
        # ✅ Output도 현재 디렉토리 기준 절대 경로
        output_name = args.output or f"report_{task_id}"
        if not os.path.isabs(output_name):
            output_name = os.path.join(current_dir, output_name)
        
        docx_path = build_document(sections_file, output_name)
        
        if docx_path:
            print(f"\n✅ Report generation complete!")
            print(f"   📄 DOCX: {docx_path}")
            print(f"   📋 Sections: {sections_file}")
    else:
        print("\n✅ Section generation complete (DOCX skipped)")


if __name__ == "__main__":
    asyncio.run(main())
