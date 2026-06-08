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

class GetParentPropertyWithoutMaxItemsOutput(pydantic.BaseModel):
    listParentPropertyWithoutMaxItems: list[str] = pydantic.Field(description = 'List of `TypeList` and `TypeSet` property names in schema without `MaxItems`')

class GetPropertyWithoutForceNewOutput(pydantic.BaseModel):
    listPropertyWithoutForceNew: list[tuple[str, str, bool, bool, int, bool]] = pydantic.Field(description = 'List of tuple, where first tuple value is the property name in schema without `ForceNew`, second tuple value is the corresponding type, third tuple value is the boolean which indicates whether the property is `Required`, fourth tuple value is the boolean which indicates whether the property has `Default` behavior, fifth tuple value is the value of `MaxItems` behavior (`0` if `MaxItems` is not specified), and sixth tuple value is the boolean which indicates whether the property is a `TypeList`, `TypeMap`, or `TypeSet` property containing `Elem` behavior with `pluginsdk.Resource`')

class EvaluateMakeFmtOutput(pydantic.BaseModel):
    bChange: bool = pydantic.Field(description = 'Whether changes are done')

class EvaluateMakeTerrafmtOutput(pydantic.BaseModel):
    bChange: bool = pydantic.Field(description = 'Whether changes are done')

class EvaluateMakeDocumentFixOutput(pydantic.BaseModel):
    bChange: bool = pydantic.Field(description = 'Whether changes are done')

class EvaluateMakeGenerateOutput(pydantic.BaseModel):
    bChange: bool = pydantic.Field(description = 'Whether changes are done')

class GetDocumentationLinkOutput(pydantic.BaseModel):
    documentationLink: str = pydantic.Field(description = 'Link of documentation corresponds to the specification')

class GetFile2ReviewOutput(pydantic.BaseModel):
    file2Review: list[str] = pydantic.Field(description = 'List of relative paths of added and changed files')

class GetChangedResourceOutput(pydantic.BaseModel):
    listChangedResource: list[str] = pydantic.Field(description = 'List of changed resources')

class GetTestRegexOutput(pydantic.BaseModel):
    testRegex: str = pydantic.Field(description = 'Combined test name regular expression pattern')

class HttpLog(pydantic.BaseModel):
    method: str
    url: str
    requestBody: str = ''
    responseBody: str = ''

class ListHttpLog(pydantic.BaseModel):
    listHttpLog: list[HttpLog]