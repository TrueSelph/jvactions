import:py logging;
import:py traceback;
import:py from logging {Logger}
import:jac from jivas.agent.action.action { Action }
import:py from .modules.google_drive_api {GoogleDriveAPI}


node GoogleDriveAction :Action: {
    has description:str = "Efficiently handles Google Drive API tasks and automation.";
    has scopes:list = ["https://www.googleapis.com/auth/drive.file"];
    has folder_id:str = "";

    has info_type:str = "service_account";
    has project_id:str = "jivas-99999";
    has private_key_id:str = "2724242c4d8ee40d99999";
    has private_key:str = "-----BEGIN PRIVATE KEY-----";
    has client_email:str = "trueselph@jivas.iam.gserviceaccount.com";
    has client_id:str = "10778319399999";
    has auth_uri:str = "https://accounts.google.com/o/oauth2/auth";
    has token_uri:str = "https://oauth2.googleapis.com/token";
    has auth_provider_x509_cert_url:str = "https://www.googleapis.com/oauth2/v1/certs";
    has client_x509_cert_url:str = "https://www.googleapis.com/robot/v1/metadata/x509/trueselph%40jivas-422314.iam.gserviceaccount.com";
    has universe_domain:str = "googleapis.com";




    can get_credentials() -> dict {

        credentials = {
            "credentials": {
                "type": self.info_type,
                "project_id": self.project_id,
                "private_key_id": self.private_key_id,
                "private_key": self.private_key,
                "client_email": self.client_email,
                "client_id": self.client_id,
                "auth_uri": self.auth_uri,
                "token_uri": self.token_uri,
                "auth_provider_x509_cert_url": self.auth_provider_x509_cert_url,
                "client_x509_cert_url": self.client_x509_cert_url,
                "universe_domain": self.universe_domain
            },
            "scopes": self.scopes,
            "folder_id": self.folder_id
        };
        return credentials;
    }


    can create_folder(folder_name:str) -> dict {
        credentials = self.get_credentials();
        folder = GoogleDriveAPI.create_folder(credentials, folder_name);
        return folder;
    }

    
    can upload_file(file_path:str, file_name:str="", folder_id:str="") -> dict {
        if not folder_id {
            folder_id = self.folder_id;
        }
        # Extract the file name from the file path if file_name is not provided
        if not file_name {
            # Split the path to get the file name and remove the extension
            file_name = file_path.split("/")[-1].split(".")[0];
        }

        credentials = self.get_credentials();
        file = GoogleDriveAPI.upload_file(credentials, file_path, file_name, folder_id);
        return file;
    }


    can upload_file_via_url(url:str, file_name:str, folder_id:str="") -> dict {
        if not folder_id {
            folder_id = self.folder_id;
        }

        credentials = self.get_credentials();
        file = GoogleDriveAPI.upload_file_via_url(credentials, url, file_name, folder_id);
        return file;
    }


    can share_file_or_folder(file_id:str, email_address:str, role:str = "reader") -> dict {
        credentials = self.get_credentials();
        share = GoogleDriveAPI.share_file_or_folder(credentials, file_id, email_address, role);
        return share;
    }


    can get_file_share_link(file_id:str="") -> dict {
        if not file_id {
            file_id = self.file_id;
        }
        credentials = self.get_credentials();
        share = GoogleDriveAPI.get_file_share_link(credentials, file_id);
        return share;
    }


    can move_to_trash(file_id:str) -> dict {
        credentials = self.get_credentials();
        move = GoogleDriveAPI.move_to_trash(credentials, file_id);
        return move;
    }

    can healthcheck() -> bool {
        try {
            if(
                self.scopes and 
                self.folder_id and 
                self.info_type and
                self.project_id and 
                self.private_key_id and 
                self.private_key and 
                self.client_email and 
                self.client_id and 
                self.auth_uri and 
                self.token_uri and 
                self.auth_provider_x509_cert_url and 
                self.client_x509_cert_url and 
                self.universe_domain
            ) {
                return True;
            }
            return False;
        } except Exception as e {
            self.logger.error(f"An exception occurred in {self.label}:\n{traceback.format_exc()}\n");
            return False;
        }
    }


}


