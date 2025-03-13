import:py logging;
import:py traceback;
import:py from logging {Logger}
import:jac from jivas.agent.action.action { Action }
import:py from .modules.google_sheet_api {GoogleSheetAPI}


node GoogleSheetAction :Action: {
    has name:str = "google_sheet_action";
    has description:str = "Efficiently handles Google Sheets API tasks and automation.";
    has key_or_url:str = "https://docs.google.com/spreadsheets/d/1ezzF1YA41LQiyY7yCEG";
    has worksheet_title:str = "Sheet1";

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
            "key_or_url": self.key_or_url,
            "worksheet_title": self.worksheet_title
        };
        return credentials;
    }


    can open_spreedsheet() -> dict {
        credentials = self.get_credentials();
        spreadsheet = GoogleSheetAPI.open_spreedsheet(credentials);
        return spreadsheet;
    }


    can open_worksheet(worksheet_title:str) -> dict {
        if not worksheet_title {
            worksheet_title = self.worksheet_title;
        }

        credentials = self.get_credentials();
        worksheet = GoogleSheetAPI.open_worksheet(credentials, worksheet_title);
        return worksheet;
    }


    can create_spreadsheet(title:str) -> dict {
        credentials = self.get_credentials();
        spreadsheet = GoogleSheetAPI.create_spreadsheet(credentials, title);
        return spreadsheet;
    }


    can create_worksheet(worksheet_title:str) -> dict {
        credentials = self.get_credentials();
        worksheet = GoogleSheetAPI.create_worksheet(credentials, worksheet_title);
        return worksheet;
    }


    can delete_worksheet(worksheet_title:str) -> dict {
        credentials = self.get_credentials();
        worksheet = GoogleSheetAPI.delete_worksheet(credentials, worksheet_title);
        return worksheet;
    }


    can share_spreadsheet(emails:list, permissions:str, role:str) -> dict {
        credentials = self.get_credentials();
        spreadsheet = GoogleSheetAPI.share_spreadsheet(credentials, emails, permissions, role);
        return spreadsheet;
    }


    can update_cell(cell:str, value:str, worksheet_title:str="") -> dict {
        if not worksheet_title {
            worksheet_title = self.worksheet_title;
        }

        credentials = self.get_credentials();
        worksheet = GoogleSheetAPI.update_cell(credentials, worksheet_title, cell, value);
        return worksheet;
    }


    can update_cell_by_coordinates(row:str, col:str, value:str, worksheet_title:str="") -> dict {
        if not worksheet_title {
            worksheet_title = self.worksheet_title;
        }

        credentials = self.get_credentials();
        worksheet = GoogleSheetAPI.update_cell_by_coordinates(credentials, worksheet_title, row, col, value);
        return worksheet;
    }


    can format_cell(cell:str, format_options:str, worksheet_title:str="") -> dict {
        if not worksheet_title {
            worksheet_title = self.worksheet_title;
        }

        credentials = self.get_credentials();
        worksheet = GoogleSheetAPI.format_cell(credentials, worksheet_title, cell, format_options);
        return worksheet;
    }


    can merge_cells(cells:str, worksheet_title:str="") -> dict {
        if not worksheet_title {
            worksheet_title = self.worksheet_title;
        }
        
        credentials = self.get_credentials();
        worksheet = GoogleSheetAPI.merge_cells(credentials, worksheet_title, cells);
        return worksheet;
    }


    can insert_rows(values:list, row_index:str, value_input_option:str="RAW", inherit_from_before:bool=False, worksheet_title:str="") -> dict {
        if not worksheet_title {
            worksheet_title = self.worksheet_title;
        }

        credentials = self.get_credentials();
        worksheet = GoogleSheetAPI.insert_rows(credentials, worksheet_title, values, row_index, value_input_option, inherit_from_before);
        return worksheet;
    }


    can batch_clear(range: list, worksheet_title:str="") -> dict {
        if not worksheet_title {
            worksheet_title = self.worksheet_title;
        }
        
        credentials = self.get_credentials();
        worksheet = GoogleSheetAPI.batch_clear(credentials, worksheet_title, range);
        return worksheet;
    }


    can find_cell(value: str, worksheet_title:str="") -> dict {
        if not worksheet_title {
            worksheet_title = self.worksheet_title;
        }
        
        credentials = self.get_credentials();
        worksheet = GoogleSheetAPI.find_cell(credentials, worksheet_title, value);
        return worksheet;
    }


    can healthcheck() -> bool {
        try {
            if(
                self.key_or_url and 
                self.worksheet_title and 
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


