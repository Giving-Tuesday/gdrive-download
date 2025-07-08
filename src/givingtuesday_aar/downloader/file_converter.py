"""File conversion utilities for AAR documents."""
# MATURE CODE. DO NOT TOUCH THIS FILE WITHOUT SPECIFIC INSTRUCTIONS

import io
from pathlib import Path
from typing import Optional, List
import mammoth
import markdownify
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


class FileConverter:
    """Converts downloaded files to markdown format."""
    
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.console = Console()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_docx_to_markdown(self, docx_path: Path) -> str:
        """Convert a DOCX file to markdown using mammoth + markdownify."""
        try:
            with open(docx_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value
            
            # Convert HTML to markdown
            markdown_content = markdownify.markdownify(html_content, heading_style="ATX")
            
            if result.messages:
                self.console.print(f"[yellow]Conversion warnings for {docx_path.name}:[/yellow]")
                for message in result.messages:
                    self.console.print(f"  {message}")
            
            return markdown_content
            
        except Exception as e:
            self.console.print(f"[red]Error converting {docx_path.name}: {e}[/red]")
            raise
    
    def convert_file(self, file_path: Path) -> Optional[Path]:
        """Convert a single file to markdown."""
        if not file_path.exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return None
        
        # Determine output path
        output_name = file_path.stem + '.md'
        output_path = self.output_dir / output_name
        
        if output_path.exists():
            self.console.print(f"[yellow]Skipping existing file: {output_name}[/yellow]")
            return output_path
        
        try:
            if file_path.suffix.lower() == '.docx':
                markdown_content = self.convert_docx_to_markdown(file_path)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                self.console.print(f"[green]Converted: {file_path.name} → {output_name}[/green]")
                return output_path
            
            else:
                self.console.print(f"[yellow]Unsupported file type: {file_path.suffix}[/yellow]")
                return None
                
        except Exception as e:
            self.console.print(f"[red]Error converting {file_path.name}: {e}[/red]")
            return None
    
    def convert_all_files(self, file_patterns: List[str] = None) -> List[Path]:
        """Convert all supported files in the input directory."""
        if file_patterns is None:
            file_patterns = ['*.docx', '*.doc']
        
        # Find all files to convert
        files_to_convert = []
        for pattern in file_patterns:
            files_to_convert.extend(self.input_dir.glob(pattern))
        
        if not files_to_convert:
            self.console.print("[yellow]No files found to convert[/yellow]")
            return []
        
        converted_files = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("Converting files...", total=len(files_to_convert))
            
            for file_path in files_to_convert:
                converted_path = self.convert_file(file_path)
                if converted_path:
                    converted_files.append(converted_path)
                
                progress.advance(task)
        
        self.console.print(f"[green]Converted {len(converted_files)} files to markdown[/green]")
        return converted_files
    
    def get_conversion_stats(self) -> dict:
        """Get statistics about the conversion process."""
        input_files = list(self.input_dir.glob('*.docx')) + list(self.input_dir.glob('*.doc'))
        output_files = list(self.output_dir.glob('*.md'))
        
        return {
            'input_files': len(input_files),
            'output_files': len(output_files),
            'conversion_rate': len(output_files) / len(input_files) if input_files else 0
        }
