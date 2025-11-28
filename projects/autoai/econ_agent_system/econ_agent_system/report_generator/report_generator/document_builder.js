#!/usr/bin/env node
/**
 * Document Builder for Multi-Agent Report Generator
 * ================================================
 * Generates professional bilingual DOCX reports from section data.
 * 
 * Usage:
 *   node document_builder.js <sections_json> [output_name]
 *   node document_builder.js report_sections_45ffab5c.json my_report
 */

const fs = require('fs');
const path = require('path');
const {
    Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
    Header, Footer, AlignmentType, PageOrientation, LevelFormat,
    HeadingLevel, BorderStyle, WidthType, PageBreak, PageNumber,
    ShadingType, TableOfContents
} = require('docx');

// ============================================================================
// Configuration
// ============================================================================

const STYLES = {
    default: {
        document: {
            run: { font: "Arial", size: 24 }  // 12pt default
        }
    },
    paragraphStyles: [
        {
            id: "Title",
            name: "Title",
            basedOn: "Normal",
            run: { size: 56, bold: true, color: "1a365d", font: "Arial" },
            paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.CENTER }
        },
        {
            id: "Heading1",
            name: "Heading 1",
            basedOn: "Normal",
            next: "Normal",
            quickFormat: true,
            run: { size: 36, bold: true, color: "2c5282", font: "Arial" },
            paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 }
        },
        {
            id: "Heading2",
            name: "Heading 2",
            basedOn: "Normal",
            next: "Normal",
            quickFormat: true,
            run: { size: 28, bold: true, color: "2d3748", font: "Arial" },
            paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 1 }
        },
        {
            id: "Heading3",
            name: "Heading 3",
            basedOn: "Normal",
            next: "Normal",
            quickFormat: true,
            run: { size: 24, bold: true, color: "4a5568", font: "Arial" },
            paragraph: { spacing: { before: 200, after: 60 }, outlineLevel: 2 }
        }
    ]
};

const NUMBERING_CONFIG = [
    {
        reference: "bullet-list",
        levels: [{
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
    },
    {
        reference: "numbered-list",
        levels: [{
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
    }
];

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Convert markdown-like text to DOCX paragraphs
 */
function textToParagraphs(text, options = {}) {
    if (!text) return [createParagraph("")];
    
    const paragraphs = [];
    const lines = text.split('\n');
    let inList = false;
    let listItems = [];
    
    for (const line of lines) {
        const trimmed = line.trim();
        
        if (!trimmed) {
            // Flush any pending list
            if (inList && listItems.length > 0) {
                paragraphs.push(...createBulletList(listItems));
                listItems = [];
                inList = false;
            }
            continue;
        }
        
        // Check for headers
        if (trimmed.startsWith('### ')) {
            paragraphs.push(createHeading(trimmed.slice(4), HeadingLevel.HEADING_3));
        } else if (trimmed.startsWith('## ')) {
            paragraphs.push(createHeading(trimmed.slice(3), HeadingLevel.HEADING_2));
        } else if (trimmed.startsWith('# ')) {
            paragraphs.push(createHeading(trimmed.slice(2), HeadingLevel.HEADING_1));
        }
        // Check for bullet points
        else if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('• ')) {
            inList = true;
            listItems.push(trimmed.slice(2));
        }
        // Check for numbered items
        else if (/^\d+\.\s/.test(trimmed)) {
            inList = true;
            listItems.push(trimmed.replace(/^\d+\.\s/, ''));
        }
        // Regular paragraph
        else {
            if (inList && listItems.length > 0) {
                paragraphs.push(...createBulletList(listItems));
                listItems = [];
                inList = false;
            }
            paragraphs.push(createParagraph(trimmed));
        }
    }
    
    // Flush remaining list items
    if (inList && listItems.length > 0) {
        paragraphs.push(...createBulletList(listItems));
    }
    
    return paragraphs;
}

function createParagraph(text, options = {}) {
    return new Paragraph({
        alignment: options.alignment || AlignmentType.JUSTIFIED,
        spacing: { after: 120, line: 276 },  // 1.15 line spacing
        children: [new TextRun({ text: text, size: options.size || 24 })]
    });
}

function createHeading(text, level) {
    return new Paragraph({
        heading: level,
        children: [new TextRun(text)]
    });
}

function createBulletList(items) {
    return items.map(item => new Paragraph({
        numbering: { reference: "bullet-list", level: 0 },
        children: [new TextRun(item)]
    }));
}

/**
 * Create section divider
 */
function createDivider() {
    return new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 240, after: 240 },
        children: [new TextRun({ text: "─".repeat(40), color: "CBD5E0" })]
    });
}

/**
 * Create bilingual section (Korean + English)
 */
function createBilingualSection(title, koreanContent, englishContent) {
    const children = [];
    
    // Section title
    children.push(createHeading(title, HeadingLevel.HEADING_1));
    
    // Korean subsection
    children.push(new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "🇰🇷 한국어", color: "2c5282" })]
    }));
    children.push(...textToParagraphs(koreanContent));
    
    // Divider
    children.push(createDivider());
    
    // English subsection
    children.push(new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "🇺🇸 English", color: "2c5282" })]
    }));
    children.push(...textToParagraphs(englishContent));
    
    // Page break after section
    children.push(new Paragraph({ children: [new PageBreak()] }));
    
    return children;
}

// ============================================================================
// Document Builder
// ============================================================================

class DocumentBuilder {
    constructor(sectionsData, metadata) {
        this.sections = sectionsData;
        this.metadata = metadata;
    }
    
    buildCoverPage() {
        const now = new Date();
        const dateStr = now.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        return [
            // Title
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 2400, after: 480 },
                children: [new TextRun({
                    text: "Multi-Agent Analysis Report",
                    bold: true,
                    size: 72,
                    color: "1a365d",
                    font: "Arial"
                })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 240 },
                children: [new TextRun({
                    text: "다중 에이전트 분석 보고서",
                    size: 48,
                    color: "4a5568",
                    font: "Arial"
                })]
            }),
            // Divider
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 480, after: 480 },
                children: [new TextRun({ text: "━".repeat(30), color: "2c5282", size: 28 })]
            }),
            // Task ID
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 120 },
                children: [new TextRun({
                    text: `Task ID: ${this.metadata.task_id || 'N/A'}`,
                    size: 24,
                    color: "718096"
                })]
            }),
            // Date
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 120 },
                children: [new TextRun({
                    text: `Generated: ${dateStr}`,
                    size: 24,
                    color: "718096"
                })]
            }),
            // Agent credits
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 720, after: 120 },
                children: [new TextRun({
                    text: "Powered by",
                    size: 20,
                    color: "a0aec0",
                    italics: true
                })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({
                    text: "Claude (Anthropic) × GPT-4 (OpenAI)",
                    size: 24,
                    color: "4a5568",
                    bold: true
                })]
            }),
            // Page break
            new Paragraph({ children: [new PageBreak()] })
        ];
    }
    
    buildTableOfContents() {
        return [
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun("Table of Contents / 목차")]
            }),
            new TableOfContents("TOC", {
                hyperlink: true,
                headingStyleRange: "1-2"
            }),
            new Paragraph({ children: [new PageBreak()] })
        ];
    }
    
    buildAllSections() {
        const allChildren = [];
        
        // Cover page
        allChildren.push(...this.buildCoverPage());
        
        // Table of Contents
        allChildren.push(...this.buildTableOfContents());
        
        // Main sections
        const sectionOrder = [
            { key: 'executive_summary', title: 'Executive Summary / 요약' },
            { key: 'introduction', title: 'Introduction / 서론' },
            { key: 'methodology', title: 'Methodology / 방법론' },
            { key: 'results', title: 'Results / 결과' },
            { key: 'discussion', title: 'Discussion / 논의' },
            { key: 'conclusion', title: 'Conclusion / 결론' }
        ];
        
        for (const { key, title } of sectionOrder) {
            const section = this.sections[key];
            if (section) {
                allChildren.push(...createBilingualSection(
                    title,
                    section.korean || '',
                    section.english || ''
                ));
            }
        }
        
        return allChildren;
    }
    
    build() {
        return new Document({
            styles: STYLES,
            numbering: { config: NUMBERING_CONFIG },
            sections: [{
                properties: {
                    page: {
                        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
                        size: { orientation: PageOrientation.PORTRAIT }
                    }
                },
                headers: {
                    default: new Header({
                        children: [new Paragraph({
                            alignment: AlignmentType.RIGHT,
                            children: [new TextRun({
                                text: "Multi-Agent Analysis Report",
                                size: 20,
                                color: "a0aec0",
                                italics: true
                            })]
                        })]
                    })
                },
                footers: {
                    default: new Footer({
                        children: [new Paragraph({
                            alignment: AlignmentType.CENTER,
                            children: [
                                new TextRun({ text: "Page ", size: 20, color: "718096" }),
                                new TextRun({ children: [PageNumber.CURRENT], size: 20, color: "718096" }),
                                new TextRun({ text: " of ", size: 20, color: "718096" }),
                                new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 20, color: "718096" })
                            ]
                        })]
                    })
                },
                children: this.buildAllSections()
            }]
        });
    }
}

// ============================================================================
// Main
// ============================================================================

async function main() {
    const args = process.argv.slice(2);
    
    if (args.length < 1) {
        console.log("Usage: node document_builder.js <sections_json> [output_name]");
        console.log("Example: node document_builder.js report_sections_45ffab5c.json my_report");
        process.exit(1);
    }
    
    const inputPath = args[0];
    const outputName = args[1] || `report_${Date.now()}`;
    
    if (!fs.existsSync(inputPath)) {
        console.error(`Error: File not found: ${inputPath}`);
        process.exit(1);
    }
    
    console.log(`\n📄 Reading sections from: ${inputPath}`);
    const data = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));
    
    console.log("🔨 Building document...");
    const builder = new DocumentBuilder(data.sections, data.metadata || {});
    const doc = builder.build();
    
    const outputPath = `${outputName}.docx`;
    console.log(`📝 Generating DOCX: ${outputPath}`);
    
    const buffer = await Packer.toBuffer(doc);
    fs.writeFileSync(outputPath, buffer);
    
    console.log(`\n✅ Report generated successfully!`);
    console.log(`   📁 Output: ${outputPath}`);
    console.log(`   📊 Size: ${(buffer.length / 1024).toFixed(1)} KB`);
}

main().catch(err => {
    console.error("Error:", err.message);
    process.exit(1);
});
