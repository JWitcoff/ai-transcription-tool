"""
File Manager - Advanced file organization and session tracking
Handles folder naming, indexing, search, and cleanup operations
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

class FileManager:
    """Manages organized file storage and session tracking"""
    
    def __init__(self, base_dir: str = "transcripts"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.index_file = self.base_dir / "index.json"
        self.max_title_length = 50
        
    def create_session_folder(self, metadata: Dict[str, Any]) -> Path:
        """
        Create organized session folder with intelligent naming
        
        Args:
            metadata: Video metadata including title, url, etc.
            
        Returns:
            Path to created session folder
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean and shorten title
        title = metadata.get('title', 'video')
        safe_title = self._sanitize_filename(title)
        
        # Add source identifier
        source_type = self._detect_source_type(metadata.get('url', ''))
        
        # Create folder name: TIMESTAMP_SOURCE_TITLE
        folder_name = f"{timestamp}_{source_type}_{safe_title}"
        
        # Handle duplicates
        folder_path = self.base_dir / folder_name
        counter = 1
        original_name = folder_name
        while folder_path.exists():
            folder_name = f"{original_name}_{counter}"
            folder_path = self.base_dir / folder_name
            counter += 1
        
        folder_path.mkdir(exist_ok=True)
        return folder_path
    
    def _sanitize_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        # Remove/replace problematic characters
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_title = re.sub(r'[^\w\s\-_()]', '', safe_title)
        safe_title = re.sub(r'\s+', '_', safe_title.strip())
        
        # Limit length
        if len(safe_title) > self.max_title_length:
            safe_title = safe_title[:self.max_title_length].rstrip('_')
        
        return safe_title or 'video'
    
    def _detect_source_type(self, url: str) -> str:
        """Detect video source type from URL"""
        if not url:
            return 'local'
        
        domain = urlparse(url).netloc.lower()
        
        if 'youtube' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'twitch' in domain:
            return 'twitch'
        elif 'vimeo' in domain:
            return 'vimeo'
        elif 'tiktok' in domain:
            return 'tiktok'
        else:
            return 'web'
    
    def register_session(self, 
                        session_path: Path,
                        metadata: Dict[str, Any],
                        analysis_info: Dict[str, Any] = None) -> None:
        """
        Register a new transcription session in the index
        
        Args:
            session_path: Path to session folder
            metadata: Video metadata
            analysis_info: Analysis information (prompt, provider, etc.)
        """
        index_data = self._load_index()
        
        session_id = session_path.name
        session_entry = {
            "id": session_id,
            "created": datetime.now().isoformat(),
            "folder_path": str(session_path.relative_to(self.base_dir)),
            "video": {
                "title": metadata.get('title', 'Unknown'),
                "url": metadata.get('url', ''),
                "duration": metadata.get('duration', 0),
                "source": self._detect_source_type(metadata.get('url', ''))
            },
            "transcription": {
                "provider": "unknown",
                "language": "auto-detected",
                "has_diarization": False
            },
            "analysis": analysis_info or {},
            "files": {
                "transcript": "transcript.txt",
                "analysis": "analysis.txt" if analysis_info else None,
                "markdown": "transcript.md",
                "raw_data": "transcript_raw.json",
                "metadata": "metadata.json"
            },
            "tags": self._generate_tags(metadata, analysis_info)
        }
        
        index_data["sessions"].append(session_entry)
        index_data["last_updated"] = datetime.now().isoformat()
        index_data["total_sessions"] = len(index_data["sessions"])
        
        self._save_index(index_data)
    
    def _generate_tags(self, metadata: Dict, analysis_info: Dict = None) -> List[str]:
        """Generate searchable tags for the session"""
        tags = []
        
        # Source tags
        source = self._detect_source_type(metadata.get('url', ''))
        tags.append(source)
        
        # Content type tags based on title
        title = metadata.get('title', '').lower()
        
        if any(word in title for word in ['interview', 'conversation', 'discussion']):
            tags.append('interview')
        if any(word in title for word in ['tutorial', 'how to', 'guide']):
            tags.append('tutorial')
        if any(word in title for word in ['podcast', 'episode']):
            tags.append('podcast')
        if any(word in title for word in ['meeting', 'conference', 'presentation']):
            tags.append('meeting')
        if any(word in title for word in ['review', 'analysis']):
            tags.append('review')
        
        # Analysis type tags
        if analysis_info and analysis_info.get('prompt'):
            prompt = analysis_info['prompt'].lower()
            if 'youtube' in prompt or 'creator' in prompt:
                tags.append('youtube-tips')
            if 'action' in prompt or 'task' in prompt:
                tags.append('action-items')
            if 'lesson' in prompt or 'tip' in prompt:
                tags.append('lessons')
            if 'summary' in prompt:
                tags.append('summary')
        
        return list(set(tags))  # Remove duplicates
    
    def _load_index(self) -> Dict:
        """Load the session index"""
        if not self.index_file.exists():
            return {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_sessions": 0,
                "sessions": []
            }
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Create new index if corrupted
            return {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_sessions": 0,
                "sessions": []
            }
    
    def _save_index(self, index_data: Dict) -> None:
        """Save the session index"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save session index: {e}")
    
    def search_sessions(self, query: str = "", 
                       source: str = "", 
                       tag: str = "",
                       limit: int = 10) -> List[Dict]:
        """
        Search through transcription sessions
        
        Args:
            query: Text to search in titles and prompts
            source: Filter by source (youtube, twitch, etc.)
            tag: Filter by tag
            limit: Maximum results to return
            
        Returns:
            List of matching sessions
        """
        index_data = self._load_index()
        sessions = index_data.get("sessions", [])
        
        results = []
        query_lower = query.lower() if query else ""
        
        for session in sessions:
            # Text search in title and analysis prompt
            if query_lower:
                title_match = query_lower in session.get("video", {}).get("title", "").lower()
                prompt_match = query_lower in session.get("analysis", {}).get("prompt", "").lower()
                
                if not (title_match or prompt_match):
                    continue
            
            # Source filter
            if source and session.get("video", {}).get("source") != source:
                continue
            
            # Tag filter
            if tag and tag not in session.get("tags", []):
                continue
            
            results.append(session)
            
            if len(results) >= limit:
                break
        
        # Sort by creation date (newest first)
        results.sort(key=lambda x: x.get("created", ""), reverse=True)
        return results
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about transcription sessions"""
        index_data = self._load_index()
        sessions = index_data.get("sessions", [])
        
        stats = {
            "total_sessions": len(sessions),
            "sources": {},
            "tags": {},
            "analysis_types": {},
            "recent_sessions": len([s for s in sessions if self._is_recent(s.get("created", ""))])
        }
        
        for session in sessions:
            # Count sources
            source = session.get("video", {}).get("source", "unknown")
            stats["sources"][source] = stats["sources"].get(source, 0) + 1
            
            # Count tags
            for tag in session.get("tags", []):
                stats["tags"][tag] = stats["tags"].get(tag, 0) + 1
            
            # Count analysis types
            prompt = session.get("analysis", {}).get("prompt", "")
            if prompt:
                analysis_type = "custom"
            else:
                analysis_type = "standard"
            stats["analysis_types"][analysis_type] = stats["analysis_types"].get(analysis_type, 0) + 1
        
        return stats
    
    def _is_recent(self, created_str: str, days: int = 7) -> bool:
        """Check if session was created recently"""
        try:
            created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
            now = datetime.now(created.tzinfo) if created.tzinfo else datetime.now()
            return (now - created).days <= days
        except:
            return False
    
    def cleanup_incomplete_sessions(self) -> int:
        """
        Clean up incomplete or corrupted session folders
        
        Returns:
            Number of folders cleaned up
        """
        cleaned = 0
        
        for folder in self.base_dir.iterdir():
            if not folder.is_dir() or folder.name == "index.json":
                continue
            
            # Check if folder has essential files
            transcript_file = folder / "transcript.txt"
            metadata_file = folder / "metadata.json"
            
            # Remove if missing essential files and older than 1 hour
            if not transcript_file.exists() or not metadata_file.exists():
                try:
                    # Check age
                    folder_time = folder.stat().st_mtime
                    age_hours = (datetime.now().timestamp() - folder_time) / 3600
                    
                    if age_hours > 1:
                        import shutil
                        shutil.rmtree(folder)
                        cleaned += 1
                        print(f"Cleaned up incomplete session: {folder.name}")
                except Exception as e:
                    print(f"Warning: Could not clean up {folder.name}: {e}")
        
        return cleaned
    
    def export_session_list(self, format: str = "markdown") -> str:
        """
        Export list of all sessions in specified format
        
        Args:
            format: 'markdown', 'json', or 'csv'
            
        Returns:
            Formatted session list
        """
        index_data = self._load_index()
        sessions = index_data.get("sessions", [])
        
        if format == "markdown":
            lines = ["# Transcription Sessions\n"]
            lines.append(f"Total Sessions: {len(sessions)}\n")
            lines.append(f"Last Updated: {index_data.get('last_updated', 'Unknown')}\n\n")
            
            for session in sessions:
                video = session.get("video", {})
                analysis = session.get("analysis", {})
                
                lines.append(f"## {video.get('title', 'Unknown')}")
                lines.append(f"- **Date**: {session.get('created', 'Unknown')[:10]}")
                lines.append(f"- **Source**: {video.get('source', 'Unknown')}")
                lines.append(f"- **URL**: {video.get('url', 'N/A')}")
                
                if analysis.get('prompt'):
                    lines.append(f"- **Analysis**: {analysis['prompt']}")
                
                lines.append(f"- **Folder**: {session.get('folder_path', '')}")
                lines.append("")
            
            return "\n".join(lines)
        
        elif format == "json":
            return json.dumps(index_data, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "Date", "Title", "Source", "URL", "Analysis Prompt", "Folder", "Tags"
            ])
            
            # Data rows
            for session in sessions:
                video = session.get("video", {})
                analysis = session.get("analysis", {})
                
                writer.writerow([
                    session.get('created', '')[:10],
                    video.get('title', ''),
                    video.get('source', ''),
                    video.get('url', ''),
                    analysis.get('prompt', ''),
                    session.get('folder_path', ''),
                    '; '.join(session.get('tags', []))
                ])
            
            return output.getvalue()
        
        else:
            return "Unsupported format. Use 'markdown', 'json', or 'csv'."