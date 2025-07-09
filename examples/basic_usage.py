#!/usr/bin/env python3
"""
Basic usage example for GivingTuesday AAR Tools.

This example demonstrates how to:
1. Download AAR documents from Google Drive
2. Convert them to markdown
3. Analyze them for challenges and successes
4. Generate comprehensive reports

All outputs are organized in a directory named after the Google Drive folder.
"""

import sys
import re
from pathlib import Path
from gdrive_download.config import GlobalConfig
from gdrive_download.downloader import GoogleDriveDownloader, FileConverter, FileRelationshipTracker
from gdrive_download.analyzer import AARAnalyzer, ReportGenerator


def sanitize_folder_name(name: str) -> str:
    """Sanitize folder name for use as directory name."""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove leading/trailing spaces and dots
    name = name.strip('. ')
    # Limit length
    if len(name) > 100:
        name = name[:100]
    # Default if empty
    if not name:
        name = "gdrive_folder"
    return name


def main():
    """Demonstrate basic AAR analysis workflow."""
    
    # Get folder URL from command line argument
    if len(sys.argv) < 2:
        print("❌ Please provide a Google Drive folder URL as an argument")
        print("Usage: python basic_usage.py <google_drive_folder_url>")
        print("Example: python basic_usage.py 'https://drive.google.com/drive/folders/FOLDER_ID'")
        return
    
    folder_url = sys.argv[1]
    
    # Configuration
    config = GlobalConfig()
    
    # First, we need to get the folder name from Google Drive
    print("🚀 Starting AAR Analysis Workflow")
    print(f"📂 Processing folder: {folder_url}")
    
    # Initial setup for credentials
    credentials_file = Path("credentials.json")
    token_file = Path("token.pickle")
    
    # Check if credentials file exists
    if not credentials_file.exists():
        print("❌ credentials.json not found!")
        print("💡 Please:")
        print("   1. Download credentials from Google Cloud Console")
        print("   2. Save as 'credentials.json' in the current directory")
        print("   3. See README.md for detailed setup instructions")
        return
    
    # Create a temporary downloader to get folder info
    temp_config = GlobalConfig()
    temp_config.downloader.credentials_file = credentials_file
    temp_config.downloader.token_file = token_file
    
    print("\n🔍 Getting folder information...")
    
    try:
        downloader = GoogleDriveDownloader(temp_config.downloader)
        folder_id = downloader.extract_folder_id(folder_url)
        
        # Get folder metadata
        folder_info = downloader.service.files().get(
            fileId=folder_id,
            fields="id,name,mimeType",
            supportsAllDrives=True
        ).execute()
        
        folder_name = folder_info.get('name', 'Unknown_Folder')
        print(f"✅ Found folder: {folder_name}")
        
    except Exception as e:
        print(f"❌ Error accessing folder: {e}")
        print("💡 Using fallback folder name based on ID")
        folder_id = downloader.extract_folder_id(folder_url)
        folder_name = f"gdrive_folder_{folder_id[:8]}"
    
    # Create sanitized directory name
    base_dir = Path(sanitize_folder_name(folder_name))
    
    # Update configuration with folder-specific paths
    config.downloader.output_dir = base_dir / "downloads"
    config.downloader.credentials_file = credentials_file
    config.downloader.token_file = token_file
    config.analyzer.input_dir = base_dir / "markdown"
    config.analyzer.output_dir = base_dir / "reports"
    
    # Create all necessary directories
    for dir_path in [base_dir, config.downloader.output_dir, 
                     config.analyzer.input_dir, config.analyzer.output_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Creating output directory structure in: {base_dir}/")
    print(f"   📥 Downloads: {config.downloader.output_dir}")
    print(f"   📝 Markdown: {config.analyzer.input_dir}")
    print(f"   📊 Reports: {config.analyzer.output_dir}")
    
    # Step 1: Download files from Google Drive
    print("\n📥 Step 1: Downloading files from Google Drive...")
    
    try:
        # List files first
        all_files = downloader.list_files_in_folder(folder_id)
        print(f"🔍 Found {len(all_files)} items in folder")
        
        # Show breakdown
        folders = [f for f in all_files if f['mimeType'] == 'application/vnd.google-apps.folder']
        files = [f for f in all_files if f['mimeType'] != 'application/vnd.google-apps.folder']
        
        print(f"🔍 Breakdown: {len(folders)} folders, {len(files)} files")
        
        if len(all_files) == 0:
            print("❌ No files found in the Google Drive folder!")
            return
        
        # Download all files
        download_results = downloader.download_folder(folder_url)
        print(f"✅ Downloaded {len(download_results)} files")
        
        # Extract URL mappings for later citation
        url_mappings = downloader.extract_all_urls(folder_url)
        print(f"📝 Extracted {len(url_mappings)} URL mappings")
        
    except Exception as e:
        print(f"❌ Error downloading files: {e}")
        return
    
    # Step 2: Convert files to markdown
    print("\n🔄 Step 2: Converting files to markdown...")
    
    converter = FileConverter(
        input_dir=config.downloader.output_dir,
        output_dir=config.analyzer.input_dir
    )
    
    converted_files = converter.convert_all_files()
    print(f"✅ Converted {len(converted_files)} files to markdown")
    
    # Step 3: Track file relationships
    print("\n🔗 Step 3: Tracking file relationships...")
    
    tracker = FileRelationshipTracker(
        downloads_dir=config.downloader.output_dir,
        markdown_dir=config.analyzer.input_dir
    )
    
    relationships = tracker.scan_file_relationships(url_mappings)
    relationships_file = base_dir / "file_relationships.csv"
    tracker.save_relationships_csv(relationships, relationships_file)
    
    print(f"✅ File relationships saved to: {relationships_file}")
    
    # Step 4: Analyze challenges and successes
    print("\n🔍 Step 4: Analyzing AAR content...")
    
    analyzer = AARAnalyzer(config.analyzer)
    
    # Analyze challenges
    challenges = analyzer.analyze_challenges()
    print(f"📊 Found {len(challenges['summary'])} challenge categories")
    
    # Analyze successes  
    successes = analyzer.analyze_successes()
    print(f"🎯 Found {len(successes['summary'])} success categories")
    
    # Generate insights
    insights = analyzer.generate_insights(challenges, successes)
    print("💡 Generated cross-cutting insights")
    
    # Step 5: Generate reports
    print("\n📋 Step 5: Generating reports...")
    
    # Create URL mapping dictionary for citations
    url_mapping_dict = {item['name']: item['url'] for item in url_mappings}
    
    report_gen = ReportGenerator(config.analyzer.output_dir, url_mapping_dict)
    file_count = analyzer.get_file_count()
    
    # Generate challenges report
    challenges_content = report_gen.generate_challenges_report(challenges, file_count)
    challenges_path = report_gen.save_report(challenges_content, "challenges_report.md")
    print(f"📄 Challenges report: {challenges_path}")
    
    # Generate successes report
    successes_content = report_gen.generate_successes_report(successes, file_count)
    successes_path = report_gen.save_report(successes_content, "successes_report.md")
    print(f"📄 Successes report: {successes_path}")
    
    # Generate insights report
    insights_content = report_gen.generate_insights_report(insights, challenges, successes)
    insights_path = report_gen.save_report(insights_content, "insights_report.md")
    print(f"📄 Insights report: {insights_path}")
    
    # Save a summary info file
    info_file = base_dir / "analysis_info.txt"
    with open(info_file, 'w') as f:
        f.write(f"AAR Analysis Summary\n")
        f.write(f"===================\n\n")
        f.write(f"Google Drive Folder: {folder_name}\n")
        f.write(f"Folder URL: {folder_url}\n")
        f.write(f"Folder ID: {folder_id}\n")
        f.write(f"Analysis Date: {Path.cwd()}\n\n")
        f.write(f"Statistics:\n")
        f.write(f"- Documents downloaded: {len(download_results)}\n")
        f.write(f"- Documents converted: {len(converted_files)}\n")
        f.write(f"- Documents analyzed: {file_count}\n")
        f.write(f"- Challenge patterns: {len(challenges['summary'])}\n")
        f.write(f"- Success patterns: {len(successes['summary'])}\n")
    
    print(f"\n✅ Analysis info saved to: {info_file}")
    
    print("\n🎉 AAR Analysis Complete!")
    print(f"📁 All outputs saved to: {base_dir}/")
    
    # Show summary statistics
    print("\n📈 Summary Statistics:")
    print(f"   • Documents analyzed: {file_count}")
    print(f"   • Challenge patterns found: {len(challenges['summary'])}")
    print(f"   • Success patterns found: {len(successes['summary'])}")
    print(f"   • Recurring challenge themes: {len(insights['challenge_themes'])}")
    print(f"   • Recurring success themes: {len(insights['success_themes'])}")


if __name__ == "__main__":
    main()