from enum import Enum


class TemplateStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TemplateVersionStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class TemplateFileFormat(str, Enum):
    PDF = "PDF"
    XLSX = "XLSX"
    XLS = "XLS"
    CSV = "CSV"
    TXT = "TXT"
    DOCX = "DOCX"
    XML = "XML"
    IMAGE = "IMAGE"


class TemplateStructureType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    HIERARCHICAL = "hierarchical"
    FORM = "form"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    MONEY = "money"
    DATE = "date"
    MONTH = "month"
    CNPJ = "cnpj"
    CPF = "cpf"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    TABLE = "table"
    CALCULATED = "calculated"
    UNKNOWN = "unknown"


class IdentificationSignalType(str, Enum):
    CONTAINS_TEXT = "contains_text"
    CONTAINS_ANY_TEXT = "contains_any_text"
    CONTAINS_ALL_TEXT = "contains_all_text"
    NOT_CONTAINS_TEXT = "not_contains_text"
    REGEX = "regex"
    FILE_FORMAT = "file_format"
    SHEET_NAME = "sheet_name"
    COLUMN_HEADER = "column_header"
    TABLE_HEADER = "table_header"
    PAGE_COUNT_RANGE = "page_count_range"
    HAS_CNPJ = "has_cnpj"
    HAS_DATE = "has_date"
    HAS_CURRENCY_VALUES = "has_currency_values"
    STRUCTURE_HINT = "structure_hint"


class AnnotationType(str, Enum):
    PDF_TEXT_BLOCK = "pdf_text_block"
    PDF_LINE = "pdf_line"
    PDF_TOKEN = "pdf_token"
    PDF_AREA = "pdf_area"
    PDF_TABLE_CANDIDATE = "pdf_table_candidate"
    EXCEL_CELL = "excel_cell"
    EXCEL_COLUMN = "excel_column"
    EXCEL_ROW = "excel_row"
    EXCEL_RANGE = "excel_range"
    EXCEL_TABLE_CANDIDATE = "excel_table_candidate"


class ExtractionStrategy(str, Enum):
    FIND_NEAR_LABEL = "find_near_label"
    FIXED_BBOX = "fixed_bbox"
    PDF_AREA_TABLE = "pdf_area_table"
    PDF_COLUMN_BY_X_POSITION = "pdf_column_by_x_position"
    HIERARCHICAL_LINES = "hierarchical_lines"
    EXCEL_CELL_ADDRESS = "excel_cell_address"
    EXCEL_COLUMN_BY_HEADER = "excel_column_by_header"
    EXCEL_RANGE_TABLE = "excel_range_table"
    EXCEL_SHEET_BY_NAME = "excel_sheet_by_name"
    REGEX_FROM_TEXT = "regex_from_text"
