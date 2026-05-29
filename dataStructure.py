import pydantic

class PreGenerateSdkOutput(pydantic.BaseModel):
    sdkExist: str = pydantic.Field(description = 'Whether SDK for resource already exists with value as `existLocally`, `existInRepo`, or `notExist`')
    sdkPackage: str = pydantic.Field(description = 'Package path of SDK to be imported according to go-azure-sdk repository')

class GenerateReplaceDirectiveOutput(pydantic.BaseModel):
    sdkPackage: str = pydantic.Field(description = 'Package path of SDK to be imported according to go-azure-sdk repository')

class GetPortalPropertyOutput(pydantic.BaseModel):
    listPortalProperty: dict[str, str] = pydantic.Field(description = 'Dictionary of resource properties according to portal screenshot, where key is the portal property and value is the corresponding specification property')

class EvaluateBasicTestOutput(pydantic.BaseModel):
    bPass: bool = pydantic.Field(description = 'Whether basic test passes')

class EvaluateCompleteTestOutput(pydantic.BaseModel):
    bPass: bool = pydantic.Field(description = 'Whether complete test passes')

class GetPropertyWithoutValidateFuncOutput(pydantic.BaseModel):
    listPropertyWithoutValidateFunc: list[tuple[str, str]] = pydantic.Field(description = 'List of tuple, where first tuple value is the property name in schema without validation function and second tuple value is the corresponding type')

class EvaluateValidateFuncTestOutput(pydantic.BaseModel):
    bAddValidateFunc: bool = pydantic.Field(description = 'Whether `ValidateFunc` is added')

class HttpLog(pydantic.BaseModel):
    method: str
    url: str
    requestBody: str = ''
    responseBody: str = ''

class ListHttpLog(pydantic.BaseModel):
    listHttpLog: list[HttpLog]