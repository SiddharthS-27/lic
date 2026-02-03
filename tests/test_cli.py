import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lic_cli.cli import (
    get_git_name,
    fetch_licenses,
    get_license,
    render_license,
    get_license_key_interactive,
    get_author_input,
    get_year_input,
    save_license,
    main,
)


class TestGetGitName:
    """Test git name retrieval"""
    
    @patch('lic_cli.cli.subprocess.run')
    def test_get_git_name_success(self, mock_run):
        """Test successful git name retrieval"""
        mock_run.return_value = MagicMock(returncode=0, stdout="John Doe\n")
        result = get_git_name()
        assert result == "John Doe"
    
    @patch('lic_cli.cli.subprocess.run')
    def test_get_git_name_failure(self, mock_run):
        """Test git name retrieval when git is not configured"""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_git_name()
        assert result is None
    
    @patch('lic_cli.cli.subprocess.run')
    def test_get_git_name_exception(self, mock_run):
        """Test git name retrieval when exception occurs"""
        mock_run.side_effect = Exception("Git not found")
        result = get_git_name()
        assert result is None


class TestFetchLicenses:
    """Test license fetching from GitHub"""
    
    @patch('lic_cli.cli.httpx.get')
    def test_fetch_licenses_success(self, mock_get):
        """Test successful license fetching"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"key": "mit", "name": "MIT License"},
            {"key": "apache-2.0", "name": "Apache License 2.0"},
            {"key": "gpl-3.0", "name": "GNU General Public License v3.0"},
        ]
        mock_get.return_value = mock_response
        
        licenses = fetch_licenses()
        
        assert "mit" in licenses
        assert "apache-2.0" in licenses
        assert "gpl-3.0" in licenses
        assert licenses["mit"]["name"] == "MIT License"
        mock_get.assert_called_once()
    
    @patch('lic_cli.cli.httpx.get')
    def test_fetch_licenses_empty(self, mock_get):
        """Test fetch when no licenses available"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        licenses = fetch_licenses()
        assert licenses == {}
    
    @patch('lic_cli.cli.httpx.get')
    def test_fetch_licenses_http_error(self, mock_get):
        """Test fetch when HTTP error occurs"""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            fetch_licenses()


class TestGetLicense:
    """Test individual license fetching"""
    
    @patch('lic_cli.cli.httpx.get')
    def test_get_license_success(self, mock_get):
        """Test successful license content retrieval"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": "MIT License content here..."
        }
        mock_get.return_value = mock_response
        
        content = get_license("mit")
        
        assert "MIT License content here..." in content
        mock_get.assert_called_once_with("https://api.github.com/licenses/mit", timeout=10.0)
    
    @patch('lic_cli.cli.httpx.get')
    def test_get_license_no_body(self, mock_get):
        """Test when license body is missing"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        content = get_license("mit")
        assert content == ""


class TestRenderLicense:
    """Test license content rendering with placeholders"""
    
    def test_render_license_year_placeholder(self):
        """Test [year] placeholder replacement"""
        content = "Copyright [year]"
        result = render_license(content, "John Doe", "2026")
        assert result == "Copyright 2026"
    
    def test_render_license_fullname_placeholder(self):
        """Test [fullname] placeholder replacement"""
        content = "Copyright [fullname]"
        result = render_license(content, "Jane Smith", "2026")
        assert result == "Copyright Jane Smith"
    
    def test_render_license_yyyy_placeholder(self):
        """Test [yyyy] placeholder replacement"""
        content = "Copyright [yyyy]"
        result = render_license(content, "John Doe", "2025")
        assert result == "Copyright 2025"
    
    def test_render_license_copyright_owner_placeholder(self):
        """Test [name of copyright owner] placeholder replacement"""
        content = "Copyright [name of copyright owner]"
        result = render_license(content, "Company Inc", "2026")
        assert result == "Copyright Company Inc"
    
    def test_render_license_uppercase_placeholder(self):
        """Test [NAME OF COPYRIGHT OWNER] placeholder replacement"""
        content = "Copyright [NAME OF COPYRIGHT OWNER]"
        result = render_license(content, "Corp", "2026")
        assert result == "Copyright Corp"
    
    def test_render_license_multiple_placeholders(self):
        """Test multiple placeholders in same content"""
        content = "Copyright [year] [fullname]. License year: [yyyy]"
        result = render_license(content, "Alice", "2026")
        assert result == "Copyright 2026 Alice. License year: 2026"
    
    def test_render_license_no_placeholders(self):
        """Test content without any placeholders"""
        content = "This is plain text"
        result = render_license(content, "John", "2026")
        assert result == "This is plain text"
    
    def test_render_license_special_characters(self):
        """Test author name with special characters"""
        content = "Copyright [fullname] [year]"
        result = render_license(content, "José García-López", "2026")
        assert result == "Copyright José García-López 2026"


class TestGetLicenseKeyInteractive:
    """Test interactive license key selection"""
    
    @patch('lic_cli.cli.questionary.select')
    def test_get_license_key_interactive_success(self, mock_select):
        """Test successful interactive selection"""
        licenses = {
            "mit": {"name": "MIT License"},
            "apache-2.0": {"name": "Apache License 2.0"}
        }
        mock_select.return_value.ask.return_value = "MIT License"
        
        key = get_license_key_interactive(licenses)
        assert key == "mit"
    
    @patch('lic_cli.cli.questionary.select')
    def test_get_license_key_interactive_cancelled(self, mock_select):
        """Test when user cancels selection"""
        licenses = {
            "mit": {"name": "MIT License"},
        }
        mock_select.return_value.ask.return_value = None
        
        key = get_license_key_interactive(licenses)
        assert key is None


class TestGetAuthorInput:
    """Test author input retrieval"""
    
    @patch('lic_cli.cli.console')
    def test_get_author_input_from_args(self, mock_console):
        """Test author from command-line arguments"""
        author = get_author_input("John Doe")
        assert author == "John Doe"
        mock_console.print.assert_called()
    
    @patch('lic_cli.cli.get_git_name')
    @patch('lic_cli.cli.questionary.text')
    @patch('lic_cli.cli.console')
    def test_get_author_input_interactive(self, mock_console, mock_text, mock_git):
        """Test interactive author input"""
        mock_git.return_value = "Git User"
        mock_text.return_value.ask.return_value = "Git User"
        
        author = get_author_input(None)
        assert author == "Git User"
    
    @patch('lic_cli.cli.get_git_name')
    @patch('lic_cli.cli.questionary.text')
    @patch('lic_cli.cli.console')
    def test_get_author_input_no_git_name(self, mock_console, mock_text, mock_git):
        """Test author input when no git name available"""
        mock_git.return_value = None
        mock_text.return_value.ask.return_value = "Manual Author"
        
        author = get_author_input(None)
        assert author == "Manual Author"


class TestGetYearInput:
    """Test year input retrieval"""
    
    @patch('lic_cli.cli.console')
    def test_get_year_input_from_args(self, mock_console):
        """Test year from command-line arguments"""
        year = get_year_input("2025")
        assert year == "2025"
    
    @patch('lic_cli.cli.questionary.text')
    @patch('lic_cli.cli.console')
    def test_get_year_input_interactive(self, mock_console, mock_text):
        """Test interactive year input"""
        mock_text.return_value.ask.return_value = str(datetime.now().year)
        
        year = get_year_input(None)
        assert year == str(datetime.now().year)
    
    @patch('lic_cli.cli.questionary.text')
    @patch('lic_cli.cli.console')
    def test_get_year_input_custom_year(self, mock_console, mock_text):
        """Test custom year input"""
        mock_text.return_value.ask.return_value = "2020"
        
        year = get_year_input(None)
        assert year == "2020"


class TestSaveLicense:
    """Test license file saving"""
    
    def test_save_license_creates_file(self, tmp_path):
        """Test that license file is created"""
        # Change to temp directory
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            content = "MIT License Content"
            save_license(content)
            
            license_file = Path("LICENSE")
            assert license_file.exists()
            assert license_file.read_text() == content
        finally:
            os.chdir(original_cwd)
    
    def test_save_license_overwrites_existing(self, tmp_path):
        """Test that existing license is overwritten"""
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            license_file = Path("LICENSE")
            license_file.write_text("Old Content")
            
            new_content = "New License Content"
            save_license(new_content)
            
            assert license_file.read_text() == new_content
        finally:
            os.chdir(original_cwd)
    
    def test_save_license_unicode_content(self, tmp_path):
        """Test saving license with unicode characters"""
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            content = "License © 2026 José García"
            save_license(content)
            
            license_file = Path("LICENSE")
            assert license_file.read_text() == content
        finally:
            os.chdir(original_cwd)


class TestMainFunction:
    """Integration tests for main function"""
    
    @patch('lic_cli.cli.save_license')
    @patch('lic_cli.cli.get_license')
    @patch('lic_cli.cli.get_year_input')
    @patch('lic_cli.cli.get_author_input')
    @patch('lic_cli.cli.fetch_licenses')
    @patch('lic_cli.cli.console')
    @patch('sys.argv', ['lic', '-l', 'mit', '-a', 'John Doe', '-y', '2026'])
    def test_main_with_all_args(self, mock_console, mock_fetch, mock_author, mock_year, 
                                mock_get_lic, mock_save):
        """Test main with all command-line arguments"""
        mock_get_lic.return_value = "MIT License Content"
        mock_author.return_value = "John Doe"
        mock_year.return_value = "2026"
        
        main()
        
        mock_save.assert_called_once()
        mock_console.print.assert_called()
    
    @patch('lic_cli.cli.save_license')
    @patch('lic_cli.cli.get_license')
    @patch('lic_cli.cli.get_year_input')
    @patch('lic_cli.cli.get_author_input')
    @patch('lic_cli.cli.get_license_key_interactive')
    @patch('lic_cli.cli.fetch_licenses')
    @patch('lic_cli.cli.console')
    @patch('sys.argv', ['lic'])
    def test_main_interactive_mode(self, mock_console, mock_fetch, mock_select_key, 
                                   mock_author, mock_year, mock_get_lic, mock_save):
        """Test main in interactive mode (no arguments)"""
        mock_fetch.return_value = {
            "mit": {"name": "MIT License"},
            "apache-2.0": {"name": "Apache License 2.0"}
        }
        mock_select_key.return_value = "mit"
        mock_author.return_value = "John"
        mock_year.return_value = "2026"
        mock_get_lic.return_value = "MIT Content"
        
        main()
        
        mock_fetch.assert_called_once()
        mock_select_key.assert_called_once()
        mock_save.assert_called_once()
    
    @patch('lic_cli.cli.save_license')
    @patch('lic_cli.cli.get_license')
    @patch('lic_cli.cli.get_year_input')
    @patch('lic_cli.cli.get_author_input')
    @patch('lic_cli.cli.fetch_licenses')
    @patch('lic_cli.cli.console')
    @patch('sys.argv', ['lic', '-l', 'mit'])
    def test_main_with_license_only(self, mock_console, mock_fetch, mock_author, 
                                    mock_year, mock_get_lic, mock_save):
        """Test main with only license argument"""
        mock_author.return_value = "John"
        mock_year.return_value = "2026"
        mock_get_lic.return_value = "MIT Content"
        
        main()
        
        mock_fetch.assert_not_called()  # Should not fetch all licenses
        mock_save.assert_called_once()
    
    @patch('lic_cli.cli.console')
    @patch('sys.argv', ['lic'])
    def test_main_keyboard_interrupt(self, mock_console):
        """Test keyboard interrupt handling"""
        with patch('lic_cli.cli.fetch_licenses', side_effect=KeyboardInterrupt):
            main()
            # Should print cancelled message
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any('Cancelled' in str(c) for c in calls)
    
    @patch('lic_cli.cli.console')
    @patch('sys.argv', ['lic', '-l', 'invalid-license'])
    def test_main_invalid_license(self, mock_console):
        """Test with invalid license key"""
        with patch('lic_cli.cli.get_license', side_effect=Exception("Not found")):
            with pytest.raises(SystemExit):
                main()


class TestCommandLineArgumentParsing:
    """Test command-line argument parsing"""
    
    @patch('lic_cli.cli.save_license')
    @patch('lic_cli.cli.get_license')
    @patch('lic_cli.cli.console')
    @patch('sys.argv', ['lic', '--help'])
    def test_help_argument(self, mock_console, mock_get, mock_save):
        """Test --help argument"""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    
    @patch('lic_cli.cli.save_license')
    @patch('lic_cli.cli.get_license')
    @patch('lic_cli.cli.get_year_input')
    @patch('lic_cli.cli.get_author_input')
    @patch('lic_cli.cli.console')
    @patch('sys.argv', ['lic', '--license', 'gpl-3.0', '--author', 'Alice', '--year', '2025'])
    def test_long_form_arguments(self, mock_console, mock_author, mock_year,
                                 mock_get, mock_save):
        """Test long-form command-line arguments"""
        mock_get.return_value = "GPL Content"
        mock_author.return_value = "Alice"
        mock_year.return_value = "2025"
        
        main()
        
        mock_save.assert_called_once()
    
    @patch('lic_cli.cli.save_license')
    @patch('lic_cli.cli.get_license')
    @patch('lic_cli.cli.get_year_input')
    @patch('lic_cli.cli.get_author_input')
    @patch('lic_cli.cli.console')
    @patch('sys.argv', ['lic', '-l', 'apache-2.0', '-a', 'Bob', '-y', '2024'])
    def test_short_form_arguments(self, mock_console, mock_author, mock_year,
                                  mock_get, mock_save):
        """Test short-form command-line arguments"""
        mock_get.return_value = "Apache Content"
        mock_author.return_value = "Bob"
        mock_year.return_value = "2024"
        
        main()
        
        mock_save.assert_called_once()


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_render_license_empty_content(self):
        """Test rendering empty license content"""
        result = render_license("", "John", "2026")
        assert result == ""
    
    def test_render_license_empty_author(self):
        """Test rendering with empty author"""
        content = "Copyright [fullname]"
        result = render_license(content, "", "2026")
        assert result == "Copyright "
    
    def test_render_license_empty_year(self):
        """Test rendering with empty year"""
        content = "Copyright [year]"
        result = render_license(content, "John", "")
        assert result == "Copyright "
    
    def test_render_license_long_author_name(self):
        """Test with very long author name"""
        long_name = "A" * 1000
        content = "Copyright [fullname]"
        result = render_license(content, long_name, "2026")
        assert long_name in result
    
    def test_render_license_duplicate_placeholders(self):
        """Test content with duplicate placeholders"""
        content = "[year] [year] [year]"
        result = render_license(content, "John", "2026")
        assert result == "2026 2026 2026"
    
    @patch('lic_cli.cli.httpx.get')
    def test_fetch_licenses_timeout(self, mock_get):
        """Test timeout during license fetch"""
        mock_get.side_effect = Exception("Timeout")
        
        with pytest.raises(Exception):
            fetch_licenses()
    
    @patch('lic_cli.cli.questionary.select')
    def test_get_license_key_single_license(self, mock_select):
        """Test interactive selection with single license"""
        licenses = {"mit": {"name": "MIT License"}}
        mock_select.return_value.ask.return_value = "MIT License"
        
        key = get_license_key_interactive(licenses)
        assert key == "mit"
