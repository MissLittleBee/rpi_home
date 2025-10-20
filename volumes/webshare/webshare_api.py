import requests
import re
import logging
import xml.etree.ElementTree as ET
import hashlib
from urllib.parse import urlencode
from passlib.hash import md5_crypt

logger = logging.getLogger(__name__)

class WebshareAPI:
    def __init__(self):
        self.base_url = 'https://webshare.cz/api'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        })
        self.logged_in = False
        self.token = None
        
    def login(self, username, password):
        """Login to webshare.cz using proper password hashing"""
        try:
            logger.info(f'Attempting login for user: {username}')
            
            # Step 1: Get salt for the user
            salt = self.get_salt(username)
            logger.info(f'Retrieved salt for user: {username}')
            
            # Step 2: Hash password using webshare algorithm
            hashed_password, digest = self.hash_password(username, password, salt)
            
            # Step 3: Perform login with hashed credentials
            login_data = {
                'username_or_email': username,
                'password': hashed_password,
                'digest': digest,
                'keep_logged_in': 1
            }
            
            login_response = self.session.post(
                f'{self.base_url}/login/',
                data=login_data
            )
            
            login_response.raise_for_status()
            
            # Parse XML response
            try:
                logger.info(f'Login response: {login_response.text[:200]}...')
                root = ET.fromstring(login_response.text)
                status_elem = root.find('status')
                
                status = status_elem.text if status_elem is not None else 'UNKNOWN'
                
                if status == 'OK':
                    # Get token from response
                    token_elem = root.find('token')
                    if token_elem is not None:
                        self.token = token_elem.text
                        self.logged_in = True
                        token_preview = self.token[:10] + "..." if self.token and len(self.token) > 10 else self.token
                        logger.info(f'Successfully logged in to Webshare.cz with token: {token_preview}')
                        return {'success': True}
                    else:
                        raise Exception("Login successful but no token received")
                else:
                    message_elem = root.find('message')
                    code_elem = root.find('code')
                    message = message_elem.text if message_elem is not None else 'No message'
                    code = code_elem.text if code_elem is not None else 'No code'
                    
                    logger.error(f'Webshare login failed: status={status}, code={code}, message={message}')
                    raise Exception(f"Login failed: {message} (code: {code})")
                    
            except ET.ParseError as e:
                logger.error(f'Failed to parse XML response: {login_response.text}')
                raise Exception(f"Login failed: Invalid server response")
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Login request error: {str(e)}')
            raise Exception(f'Login failed: Network error - {str(e)}')
        except Exception as e:
            logger.error(f'Login error: {str(e)}')
            raise Exception(f'Login failed: {str(e)}')
    
    def get_salt(self, username):
        """Retrieves salt for password hash from webshare.cz"""
        try:
            data = {'username_or_email': username}
            response = self.session.post(f'{self.base_url}/salt/', data=data)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            status_elem = root.find('status')
            
            if status_elem is not None and status_elem.text == 'OK':
                salt_elem = root.find('salt')
                if salt_elem is not None:
                    return salt_elem.text
                else:
                    raise Exception("No salt found in response")
            else:
                message_elem = root.find('message')
                message = message_elem.text if message_elem is not None else 'Unknown error'
                raise Exception(f"Failed to get salt: {message}")
                
        except Exception as e:
            logger.error(f'Salt request error: {str(e)}')
            raise Exception(f'Failed to get salt: {str(e)}')
    
    def hash_password(self, username, password, salt):
        """Creates password hash used by Webshare API"""
        try:
            # Step 1: Create MD5 crypt hash with salt
            md5_hash = md5_crypt.encrypt(password, salt=salt)
            
            # Step 2: SHA1 hash of the MD5 crypt result
            password_hash = hashlib.sha1(md5_hash.encode('utf-8')).hexdigest()
            
            # Step 3: Create digest for authentication
            digest_string = f"{username}:Webshare:{password_hash}"
            digest = hashlib.md5(digest_string.encode('utf-8')).hexdigest()
            
            return password_hash, digest
            
        except Exception as e:
            logger.error(f'Password hashing error: {str(e)}')
            raise Exception(f'Failed to hash password: {str(e)}')
    
    def search(self, query):
        """Search for files on webshare.cz"""
        try:
            if not self.logged_in or not self.token:
                raise Exception('Not logged in. Please login first.')
            
            search_data = {
                'what': query,
                'category': '',
                'sort': 'largest',
                'order': 'desc',
                'wst': self.token
            }
            
            response = self.session.post(f'{self.base_url}/search/', data=search_data)
            
            response.raise_for_status()
            
            # Parse XML response
            try:
                root = ET.fromstring(response.text)
                status_elem = root.find('status')
                status = status_elem.text if status_elem is not None else 'UNKNOWN'
                
                if status == 'OK':
                    return self._parse_search_results_xml(root)
                else:
                    message_elem = root.find('message')
                    message = message_elem.text if message_elem is not None else 'Unknown error'
                    raise Exception(f"Search failed: {message}")
                    
            except ET.ParseError as e:
                logger.error(f'Failed to parse search XML response: {response.text}')
                raise Exception(f"Search failed: Invalid server response")
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Search request error: {str(e)}')
            raise Exception(f'Search failed: Network error - {str(e)}')
        except Exception as e:
            logger.error(f'Search error: {str(e)}')
            raise Exception(f'Search failed: {str(e)}')
    
    def _parse_search_results(self, data):
        """Parse search results from API response (legacy JSON)"""
        results = []
        
        files = data.get('files', [])
        for file_info in files:
            result = {
                'id': file_info.get('ident', ''),
                'name': file_info.get('name', ''),
                'size': file_info.get('size', 0),
                'sizeFormatted': self._format_file_size(file_info.get('size', 0)),
                'type': file_info.get('type', 'unknown'),
                'downloads': file_info.get('download_count', 0),
                'rating': file_info.get('rating', 0),
                'date': file_info.get('date_added', '')
            }
            results.append(result)
        
        return results
    
    def _parse_search_results_xml(self, root):
        """Parse search results from XML response"""
        results = []
        
        # Look for file entries in XML
        files = root.findall('.//file') or root.findall('.//item')
        
        for file_elem in files:
            def get_elem_text(elem_name, default=''):
                elem = file_elem.find(elem_name)
                return elem.text if elem is not None else default
            
            def get_elem_int(elem_name, default=0):
                try:
                    return int(get_elem_text(elem_name, str(default)))
                except (ValueError, TypeError):
                    return default
            
            result = {
                'id': get_elem_text('ident') or get_elem_text('id'),
                'name': get_elem_text('name') or get_elem_text('filename'),
                'size': get_elem_int('size'),
                'sizeFormatted': self._format_file_size(get_elem_int('size')),
                'type': get_elem_text('type', 'unknown'),
                'downloads': get_elem_int('download_count') or get_elem_int('downloads'),
                'rating': get_elem_int('rating'),
                'date': get_elem_text('date_added') or get_elem_text('date')
            }
            results.append(result)
        
        return results
    
    def initiate_download(self, file_id):
        """Get download link for a file"""
        try:
            if not self.logged_in or not self.token:
                raise Exception('Not logged in. Please login first.')
            
            download_data = {
                'ident': file_id,
                'wst': self.token
            }
            
            response = self.session.post(f'{self.base_url}/file_link/', data=download_data)
            
            response.raise_for_status()
            
            # Parse XML response
            try:
                root = ET.fromstring(response.text)
                status_elem = root.find('status')
                status = status_elem.text if status_elem is not None else 'UNKNOWN'
                
                if status == 'OK':
                    link_elem = root.find('link')
                    name_elem = root.find('name')
                    size_elem = root.find('size')
                    
                    size_text = size_elem.text if size_elem is not None else '0'
                    file_size = 0
                    try:
                        if size_text and size_text.isdigit():
                            file_size = int(size_text)
                    except (ValueError, AttributeError):
                        file_size = 0
                    
                    return {
                        'downloadUrl': link_elem.text if link_elem is not None else '',
                        'fileName': name_elem.text if name_elem is not None else 'download',
                        'fileSize': file_size
                    }
                else:
                    message_elem = root.find('message')
                    message = message_elem.text if message_elem is not None else 'Unknown error'
                    raise Exception(f"Download failed: {message}")
                    
            except ET.ParseError as e:
                logger.error(f'Failed to parse download XML response: {response.text}')
                raise Exception(f"Download failed: Invalid server response")
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Download request error: {str(e)}')
            raise Exception(f'Download failed: Network error - {str(e)}')
        except Exception as e:
            logger.error(f'Download error: {str(e)}')
            raise Exception(f'Download failed: {str(e)}')
    
    def download_file(self, file_id, download_path, filename=None):
        """Download file from webshare.cz to local path"""
        import os
        
        try:
            # Get download URL first
            download_info = self.initiate_download(file_id)
            download_url = download_info['downloadUrl']
            
            if not filename:
                filename = download_info['fileName']
            
            # Ensure download directory exists
            os.makedirs(download_path, exist_ok=True)
            
            # Full file path
            file_path = os.path.join(download_path, filename)
            
            # Download the file
            logger.info(f'Starting download of {filename}...')
            
            response = self.session.get(download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
            
            # Set proper file permissions (readable by group and others)
            try:
                os.chmod(file_path, 0o644)
                logger.info(f'Set file permissions to 644 for {filename}')
            except Exception as e:
                logger.warning(f'Could not set file permissions for {filename}: {str(e)}')
            
            logger.info(f'Download completed: {filename} ({self._format_file_size(downloaded_size)})')
            
            return {
                'fileName': filename,
                'filePath': file_path,
                'size': downloaded_size
            }
            
        except Exception as e:
            logger.error(f'Download failed: {str(e)}')
            raise Exception(f'Download failed: {str(e)}')
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if not size_bytes:
            return '0 B'
        
        size_names = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while size_bytes >= 1024.0 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"