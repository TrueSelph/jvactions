"""This module contains the GoogleSheetAPI class which is used to interact with the Google Sheets API."""

import logging
import traceback
from typing import Optional, Union

import gspread


class GoogleSheetAPI:
    """Class for interacting with the Google Sheets API."""

    logger = logging.getLogger(__name__)

    @staticmethod
    def open_spreadsheet(creds: dict, gc: gspread.Client = None) -> gspread.Spreadsheet:
        """Opens a Google Spreadsheet."""
        if gc is None:
            gc = gspread.service_account_from_dict(creds["credentials"])

        if "http" in creds["key_or_url"]:
            response = gc.open_by_url(creds["key_or_url"])
        else:
            response = gc.open_by_key(creds["key_or_url"])
        return response

    @staticmethod
    def open_worksheet(creds: dict, worksheet_title: str = "") -> Union[list, dict]:
        """Opens a worksheet and returns all records."""
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            response = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds["worksheet_title"]

            worksheet = response.worksheet(worksheet_title)
            return worksheet.get_all_records()
        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to open worksheet: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def create_spreadsheet(creds: dict, title: str) -> Union[str, dict]:
        """Creates a new Google Spreadsheet."""
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            sh = gc.create(title)
            return sh.id
        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to create spreadsheet: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def create_worksheet(creds: dict, title: str) -> Union[str, dict]:
        """Creates a new worksheet in an existing Google Spreadsheet."""
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            worksheet = sh.add_worksheet(title=title, rows=100, cols=20)
            return worksheet.id
        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to create worksheet: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def delete_worksheet(creds: dict, worksheet_title: str) -> Union[bool, dict]:
        """Deletes a worksheet from an existing Google Spreadsheet."""
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            worksheet = sh.worksheet(worksheet_title)
            result = sh.del_worksheet(worksheet)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to delete worksheet: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def share_spreadsheet(
        creds: dict, emails: Union[str, list], permissions: str = "", role: str = ""
    ) -> Union[list, dict]:
        """
        Share a spreadsheet with one or more users.
        example:
        GoogleSheetAPI.share_spreadsheet(data, "otto@example.com", "user", "writer")
        """
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            shs = []
            if isinstance(emails, list):
                for email in emails:
                    result = sh.share(email, perm_type=permissions, role=role)
                    shs.append(result)
            else:
                result = sh.share(emails, perm_type=permissions, role=role)
                shs.append(result)

            return shs
        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to share spreadsheet: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def update_cell(
        creds: dict, worksheet_title: str = "", cell: str = "", value: str = ""
    ) -> Union[dict, dict]:
        """
        Updates a cell or a range of cells in the specified worksheet.

        Examples:
        - update_cell(data, "Sheet4", "A8:B9", [["Testing", "Testing2"], ["Testing", "Testing2"]])
        - update_cell(data, "Sheet4", "A8", "testing!!")
        """
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds["worksheet_title"]

            worksheet = sh.worksheet(worksheet_title)
            result = worksheet.update(
                cell,
                value,
                value_input_option=gspread.utils.ValueInputOption.user_entered,
            )
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to update cell: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def update_cell_by_coordinates(
        creds: dict,
        worksheet_title: str = "",
        row: int = 0,
        col: int = 0,
        value: str = "",
    ) -> Union[dict, dict]:
        """
        Updates a cell by coordinates in the specified worksheet.

        Examples:
        - update_cell_by_coordinates(data, "Sheet4", 1, 4, "Bingo!!")
        """
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds["worksheet_title"]

            worksheet = sh.worksheet(worksheet_title)
            result = worksheet.update_cell(row, col, value)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to update cell: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def format_cell(
        creds: dict,
        worksheet_title: str = "",
        cell: str = "",
        format_options: Optional[dict] = None,
    ) -> Union[dict, dict]:
        """
        Formats a cell or a range of cells in the specified worksheet.

        Examples:
        - format_cell(data, "Sheet4", "A8", {'textFormat': {'bold': True}})
        """
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds["worksheet_title"]

            worksheet = sh.worksheet(worksheet_title)
            result = worksheet.format(cell, format_options)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to format cell: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def merge_cells(
        creds: dict, worksheet_title: str = "", cells: str = ""
    ) -> Union[dict, dict]:
        """Merges cells in the specified worksheet."""
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds["worksheet_title"]

            worksheet = sh.worksheet(worksheet_title)
            result = worksheet.merge_cells(cells)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to merge cells: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def insert_rows(
        creds: dict,
        worksheet_title: str,
        values: list[list],
        row_index: str = "",
        value_input_option: str = "RAW",
        inherit_from_before: bool = False,
    ) -> Union[dict, dict]:
        """Inserts rows into the specified worksheet."""
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds["worksheet_title"]

            worksheet = sh.worksheet(worksheet_title)
            result = worksheet.insert_rows(
                values, row_index, value_input_option, inherit_from_before
            )
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to insert rows: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def batch_clear(
        creds: dict, worksheet_title: str, range: list
    ) -> Union[dict, dict]:
        """Clears a range of cells in the specified worksheet."""
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds["worksheet_title"]

            worksheet = sh.worksheet(worksheet_title)
            result = worksheet.batch_clear(range)
            return result
        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to batch clear: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def find_cell(creds: dict, worksheet_title: str, value: str) -> Union[dict, dict]:
        """Finds a cell in the specified worksheet."""
        try:
            # build service
            gc = gspread.service_account_from_dict(creds["credentials"])

            # action
            sh = GoogleSheetAPI.open_spreadsheet(creds, gc)
            if not worksheet_title:
                worksheet_title = creds["worksheet_title"]

            worksheet = sh.worksheet(worksheet_title)
            res = worksheet.find(value)

            return {"status": 200, "row": res.row, "column": res.col}

        except Exception as e:
            GoogleSheetAPI.logger.error(
                f"unable to find cell: {traceback.format_exc()}"
            )
            return {"error": str(e)}
