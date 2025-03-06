import gspread
import logging
import traceback


class GoogleSheetAPI:
    
    logger = logging.getLogger(__name__)
    
    @staticmethod
    def open_spreadsheet(creds, gc=""):
        if not gc:
            gc = gspread.service_account_from_dict(creds['credentials'])
            
        if "http" in creds['key_or_url']:
            response = gc.open_by_url(creds['key_or_url'])
        else:
            response = gc.open_by_key(creds['key_or_url'])
        return response
    
        
    @staticmethod
    def open_worksheet(creds, worksheet_title=""):
        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])

            # action
            response = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds['worksheet_title']

            worksheet = response.worksheet(worksheet_title)
            return worksheet.get_all_records()
        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to open worksheet: {traceback.format_exc()}")
            return {'error': e}
        
        
    @staticmethod
    def create_spreadsheet(creds, title):

        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])
            
            # action
            sh = gc.create(title)
            return sh.id
        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to create spreadsheet: {traceback.format_exc()}")
            return {'error': e}


    @staticmethod
    def create_worksheet(creds, title):
        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])
            
            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            worksheet = sh.add_worksheet(title=title, rows=100, cols=20)
            return worksheet.id
        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to create worksheet: {traceback.format_exc()}")
            return {'error': e}

    @staticmethod
    def delete_worksheet(creds, worksheet_title):
        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])
            
            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            worksheet = sh.worksheet(worksheet_title)
            result = sh.del_worksheet(worksheet)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to delete worksheet: {traceback.format_exc()}")
            return {'error': e}


    @staticmethod
    def share_spreadsheet(creds, emails, permissions="", role=""):
        """
        Share a spreadsheet with one or more users.
        example:
        GoogleSheetAPI.share_spreadsheet(data, "otto@example.com", "user", "writer")
        """
        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            shs = []
            if type(emails) == list:
                for email in emails:
                    result = sh.share(email, perm_type=permissions, role=role)
                    shs.append(result)
            else:
                result = sh.share(emails, perm_type=permissions, role=role)
                shs.append(result)

            return shs
        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to share spreadsheet: {traceback.format_exc()}")
            return {'error': e}


    @staticmethod
    def update_cell(creds, worksheet_title="", cell="", value=""):
        """
        Updates a cell or a range of cells in the specified worksheet.

        Examples:
        - update_cell(data, "Sheet4", "A8:B9", [["Testing", "Testing2"], ["Testing", "Testing2"]])
        - update_cell(data, "Sheet4", "A8", "testing!!")
        """
        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds['worksheet_title']

            worksheet = sh.worksheet(worksheet_title)
            result = worksheet.update(cell, value, value_input_option=gspread.utils.ValueInputOption.user_entered)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to update cell: {traceback.format_exc()}")
            return {'error': e}

    @staticmethod
    def update_cell_by_coordinates(creds, worksheet_title="", row="", col="", value=""):
        """
        Updates a cell by coordinates in the specified worksheet.

        Examples:
        - update_cell_by_coordinates(data, "Sheet4", "1", "4", "Bingo!!")
        """
        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds['worksheet_title']

            worksheet = sh.worksheet(worksheet_title)
            row = int(row)
            col = int(col)
            result = worksheet.update_cell(row, col, value)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to update cell: {traceback.format_exc()}")
            return {'error': e}

    @staticmethod
    def format_cell(creds, worksheet_title="", cell="", format_options=""):
        """
        Formats a cell or a range of cells in the specified worksheet.

        Examples:
        - format_cell(data, "Sheet4", "A8", {'textFormat': {'bold': True}})
        """
        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds['worksheet_title']

            worksheet = sh.worksheet(worksheet_title)
            result = worksheet.format(cell, format_options)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to format cell: {traceback.format_exc()}")
            return {'error': e}


    @staticmethod
    def merge_cells(creds, worksheet_title="", cells=""):
        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds['worksheet_title']

            worksheet = sh.worksheet(worksheet_title)
            result = worksheet.merge_cells(cells)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to merge cells: {traceback.format_exc()}")
            return {'error': e}



    @staticmethod
    def insert_rows(creds, worksheet_title: str, values: list[list], row_index="", value_input_option="RAW", inherit_from_before=False):
        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds['worksheet_title']

            worksheet = sh.worksheet(worksheet_title)
            result = worksheet.insert_rows(values, row_index, value_input_option, inherit_from_before)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to insert rows: {traceback.format_exc()}")
            return {'error': e}
            
            
    @staticmethod
    def batch_clear(creds, worksheet_title: str, range: list):
        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds['worksheet_title']

            worksheet = sh.worksheet(worksheet_title)
            result = worksheet.batch_clear(range)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to batch clear: {traceback.format_exc()}")
            return {'error': e}
            
            
    @staticmethod
    def find_cell(creds, worksheet_title: str, value: str):
        try:
            # build service
            gc = gspread.service_account_from_dict(creds['credentials'])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds['worksheet_title']

            worksheet = sh.worksheet(worksheet_title)
            res = worksheet.find(value)

            return {
                "status": 200,
                "row": res.row,
                "column": res.col
            }

        except Exception as e:
            GoogleSheetAPI.logger.error(f"unable to find cell: {traceback.format_exc()}")
            return {'error': e}


