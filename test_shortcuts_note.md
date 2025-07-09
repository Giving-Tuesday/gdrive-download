# Creating Shortcuts - Authentication Required

The shortcuts feature requires write permissions to Google Drive. 

## Steps to enable:

1. **Delete the old token** (already done):
   ```bash
   rm token.pickle
   ```

2. **Run the search command with shortcuts**:
   ```bash
   source .venv/bin/activate
   python /Users/pricemat/src/gdrive-download/src/givingtuesday_aar/cli/search.py -p "Project Brief*" --no-download --create-shortcuts 1l6STAueoQ1zMbnxpcAlvBK7YSC4nOvjy
   ```

3. **Re-authenticate** when prompted:
   - A browser window will open
   - Log in to your Google account
   - Grant the new permissions (now includes write access)
   - The token will be saved for future use

## What changed:

- Updated scope from `drive.readonly` to `drive` in the GoogleDriveDownloader
- This allows creating shortcuts (which are a type of file creation)
- The same authentication will work for all features (search, download, and shortcuts)

## Usage:

Once authenticated, you can:
- Create shortcuts without downloading: `--no-download --create-shortcuts FOLDER_ID`
- Search, download, AND create shortcuts: `--create-shortcuts FOLDER_ID`
- The shortcuts will be named with "[Drive Name]" prefix for files from shared drives