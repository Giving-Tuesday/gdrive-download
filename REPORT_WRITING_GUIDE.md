# AAR Report Writing Guide

This guide helps you create comprehensive After Action Review reports using the extracted data from the AAR analysis tools.

## Voice and Audience Guidelines

**Internal Reports** (for organizational learning):
- Use first-person organizational voice ("we", "our work", "our challenges")
- Direct, conversational tone
- Focus on practical insights over analysis
- Acknowledge limitations honestly ("not all our leaders", "if problems were easy to solve...")

**External Reports** (for stakeholders/partners):
- Use third-person analytical voice ("the organization", "GivingTuesday demonstrates")
- Professional but not overly formal tone
- Balance strengths with challenges

**Length Targets**:
- Executive summary: 2-3 paragraphs max
- Total report: 8-12 pages for comprehensive analysis
- Avoid excessive elaboration - make your point and move on

## Overview

The analysis tools have extracted structured data from your AAR documents into several files that support manual report writing. This approach ensures high-quality, meaningful reports with proper context and insights.

## Generated Data Files

After running `aar-extract-data`, you'll find these files in your output directory:

### 1. `analysis_summary.json`
**Purpose**: High-level overview of the entire collection
**Contents**:
- Total document count and word count
- Documents with improvement/success sections
- Most common keywords for challenges and successes
- Distribution of files by year

**Use**: Start here for overall statistics and scope

### 2. `document_statistics.json`
**Purpose**: Detailed statistics about the document collection
**Contents**:
- Analysis metadata (date, totals)
- Document categorization (by type, year)
- Average document length and distribution

**Use**: Understanding the scope and nature of your document collection

### 3. `improvement_sections.json`
**Purpose**: Raw text of all "improvement" sections extracted from AARs
**Contents**:
- File-by-file breakdown of improvement sections
- Complete text of relevant sections (not fragments)
- Various section header types captured

**Use**: Primary source for identifying challenge patterns and specific improvement needs

### 4. `success_sections.json`
**Purpose**: Raw text of all "success" sections extracted from AARs
**Contents**:
- File-by-file breakdown of success sections
- Complete text of relevant sections
- What went well, strengths, achievements sections

**Use**: Primary source for identifying success patterns and organizational strengths

### 5. `keyword_analysis.json`
**Purpose**: Frequency analysis of challenge and success-related keywords
**Contents**:
- Most common challenge keywords with counts
- Most common success keywords with counts
- Total mention counts

**Use**: Identifying high-level themes and priorities

### 6. `file_metadata.csv`
**Purpose**: Technical metadata for each document
**Contents**:
- Filename, word count, line count
- Modification date, file size
- Sorted by document length

**Use**: Understanding document scope, identifying unusually long/short documents

## Report Writing Process

### Step 1: Initial Review
1. **Read `analysis_summary.json`** to understand the scope
2. **Review `keyword_analysis.json`** to identify major themes
3. **Scan `file_metadata.csv`** to understand document distribution

### Step 2: Deep Dive Analysis

#### For Challenge Reports:
1. **Open `improvement_sections.json`**
2. **Read through each document's improvement sections**
3. **Look for recurring patterns across multiple documents**:
   - Resource/capacity issues
   - Communication problems
   - Timeline/planning challenges
   - Partnership difficulties
   - Technical/operational issues
4. **Group similar challenges together**
5. **Identify the most frequent and impactful challenges**
6. **Select representative quotes (complete sentences/paragraphs)**

#### For Success Reports:
1. **Open `success_sections.json`**
2. **Read through each document's success sections**  
3. **Look for recurring strengths across multiple documents**:
   - Leadership development
   - Innovation and creativity
   - Effective partnerships
   - Strong execution
   - Community engagement
4. **Group similar successes together**
5. **Identify consistent organizational capabilities**
6. **Select representative quotes (complete sentences/paragraphs)**

### Step 3: Report Structure

#### Recommended Challenge Report Structure:
```markdown
# Persistent Challenges Across GivingTuesday AARs

## Executive Summary
- Brief overview of the analysis scope
- Top 3-5 challenge categories identified
- Key insights about systemic vs. isolated issues

## Challenge Categories

### [Category Name] (e.g., "Resource and Capacity Constraints")
- Description of the challenge
- Frequency across documents
- Impact assessment
- Representative quotes from multiple AARs
- Specific examples

### [Repeat for each major category]

## Cross-Cutting Patterns
- Themes that appear across multiple categories
- Root cause analysis
- Interconnected challenges

## Recommendations
- Systemic improvements
- Process changes
- Resource allocation suggestions
- Specific actionable steps

## Methodology
- Number of documents analyzed
- Time period covered
- Analysis approach
```

#### Recommended Success Report Structure:
```markdown
# Organizational Strengths and Successes Across GivingTuesday AARs

## Executive Summary
- Brief overview of analysis scope
- Top organizational strengths identified
- Key insights about consistent capabilities

## Core Strengths

### [Strength Name] (e.g., "Adaptive Leadership Development")
- Description of the strength
- Evidence across multiple documents
- Impact and outcomes
- Representative quotes from multiple AARs
- Specific examples

### [Repeat for each major strength]

## Success Multiplication Patterns
- How successes build on each other
- Consistent approaches that work
- Scalable practices

## Recommendations for Amplification
- How to scale successful approaches
- Systematic application of strengths
- Areas for expanded focus

## Methodology
- Number of documents analyzed
- Time period covered
- Analysis approach
```

### Step 4: Quality Guidelines

#### Quote Selection:
- **Use complete sentences or paragraphs**
- **Provide sufficient context**
- **Choose representative examples, not outliers**
- **Vary sources across different documents/teams**
- **Ensure quotes actually support your point**

#### Analysis Depth:
- **Look for patterns across multiple documents**
- **Distinguish between systemic and isolated issues**
- **Consider frequency AND impact**
- **Balance criticism with constructive framing**
- **Connect findings to actionable recommendations**

#### Citation Format:
- Use the Google Drive URLs from your file relationship data
- Format: `*"Quote text"* ([Document Name](Google Drive URL))`
- Ensure URLs are accessible to your audience

## Writing Quality Standards
- **Be direct**: Avoid academic language and excessive qualifiers
- **Show, don't tell**: Use specific quotes, not general praise
- **Stay grounded**: Acknowledge real problems without minimizing them
- **Focus on learning**: Frame as organizational reflection, not external judgment
- **Include citations**: All quotes must include document name and Google Drive URL

### Streamlined Synthetic Report Structure:
```markdown
# [Organization] Organizational Learning Report

## Executive Summary (2-3 paragraphs max)
- Core strengths identified
- Key challenges and their connection to strengths
- Basic recommendations

## Core Strengths (3-4 areas)
### [Strength Name]
- What we do well
- Evidence from multiple AARs
- How this enables other work

## Challenge Areas (3-4 areas) 
### [Challenge Name]
- Where we struggle
- How this connects to our strengths ("flip side" relationship)
- Specific examples

## Closing Thoughts
- Realistic next steps
- Acknowledgment that improvement takes time
- Focus on organizational learning

## Methodology
- Brief analysis approach
- Honest about limitations
```

### Key Principles for Reports:

1. **Lead with strengths** but don't oversell them
2. **Connect challenges to strengths** - show flip-side relationships  
3. **Use organizational voice** for internal reports
4. **Keep it practical** - avoid elaborate strategic frameworks
5. **Be honest about limitations** and ongoing difficulties

## Advanced Analysis Techniques

### Temporal Analysis:
- Compare 2023 vs 2024 vs 2025 documents
- Identify evolving challenges/improving areas
- Track progress on specific issues

### Team/Hub Analysis:
- Group findings by region (Africa, India, US/CA, etc.)
- Identify location-specific vs universal patterns
- Compare approaches across different contexts

### Document Type Analysis:
- Compare day-of AARs vs project AARs vs retreat AARs
- Identify patterns specific to different activity types
- Understand context-dependent challenges/successes

## Tips for Effective Reports

1. **Start with the data, not preconceptions**
2. **Let patterns emerge from multiple sources**
3. **Use specific examples, avoid generalizations**
4. **Consider your audience - what can they actually do?**
5. **Acknowledge limitations honestly**
6. **Treat challenges as shared problems to solve, not individual failures**

## Next Steps After Report Writing

1. **Share draft reports with key stakeholders for feedback**
2. **Validate findings with people mentioned in the AARs**
3. **Develop action plans based on recommendations**
4. **Plan follow-up analysis to track progress**
5. **Create process improvements based on insights**

---

*This guide supports the GivingTuesday AAR Analysis Tools. For technical questions about the data extraction, see the main README.md.*
