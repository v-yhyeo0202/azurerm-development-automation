import pydantic

class PreGenerateSdkOutput(pydantic.BaseModel):
    bSdkExist: bool = pydantic.Field(description = 'Whether SDK for resource already exists')
    sdkPackage: str = pydantic.Field(description = 'Package path of SDK to be imported according to go-azure-sdk repository')

class GetPortalPropertyOutput(pydantic.BaseModel):
    listPortalProperty: dict[str, str] = pydantic.Field(description = 'Dictionary of resource properties according to portal screenshot, where key is the portal property and value is the corresponding specification property')