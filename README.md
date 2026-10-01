# AzureRM Development Automation

This is an automation application aims to automate the development in [`terraform-provider-azurerm` repository](https://github.com/hashicorp/terraform-provider-azurerm). The application runs in workflow style with LLM SDK, bash scripts, services, and Python function calls.

## Steps

1. Install [Python](https://www.python.org/downloads/).

2. Clone this repository and run the installation script.
    ```bash
    git clone https://github.com/v-yhyeo0202/azurerm-development-automation
    cd azurerm-development-automation
    ./install.sh
    ```

3. As [`copilot-sdk`](https://github.com/github/copilot-sdk) is used, set the environment variable [`COPILOT_GITHUB_TOKEN`](https://github.com/github/copilot-sdk/blob/main/docs/auth/authenticate.md#environment-variables).

4. Configure [`config.yml`](#configurations).

5. Activate virtual environment and run the workflow. The changes will be done in `terraform-provider-azurerm` submodule.
    ```bash
    source venv-azurerm-development-automation/bin/activate
    python main.py
    ```

## Configurations

Before running the workflow, `config.yml` has to be configured according to the definition below.
* `path.main`: Path of this repository directory.
* `path.service`: Path of service directory in relative to [`terraform-provider-azurerm` submodule](https://github.com/hashicorp/terraform-provider-azurerm).
* `defaultModel`: Default model to be used for [`copilot-sdk`](https://github.com/github/copilot-sdk).
* `resource`: Resource name without `azurerm_` prefix.
* `clientResource`: Resource name to be printed in error message of `terraform-provider-azurerm/internal/services/{service}/client/client.go`.
* `specification`: Link of resource OpenAPI specification from [`azure-rest-api-specs` repository](https://github.com/Azure/azure-rest-api-specs/tree/main/specification).
* `clientServiceName`: Service name to be added in `Name` and `WebsiteCategories` methods of `terraform-provider-azurerm/internal/services/{service}/registration.go`.
* `pandoraService`: Service to be added in `pandora/config/resource-manager.hcl`. Only set this if lowercase `pandoraServiceName` is not same as `pandoraService` configuration.
* `pandoraServiceName`: Service name to be added in `pandora/config/resource-manager.hcl`.
* `sdkServiceName`: Service name according to `go-azure-sdk/resource-manager`.
* `resourceGroupName`: Name of existing resource group containing the targeted resource.
* `nHttpProxy`: Number of HTTP proxies to monitor parallel test HTTP traffic. The maximum number is equal to the length of `port.httpProxy`.
* `port.datApi`: Port number to be used for data API server of [`pandora` submodule](https://github.com/hashicorp/pandora).
* `port.httpProxy.#.sender`: Port number to be used for mitmproxy to monitor parallel test HTTP traffic.
* `port.httpProxy.#.listener`: Port number to be used for listening HTTP traffic logs from mitmproxy.
* `flow`: [Workflow](#Workflows) to be run.

## Workflows

Several workflows are provided in this automation application as shown below with their corresponding configurations.
* `aiAssistedDevelopment2ReplaceDirective`
    * Update [AzureRM AI assisted development](https://github.com/WodansSon/terraform-azurerm-ai-assisted-development).
    * Generate new client and service files.
* `sdkImport2PortalProperty`
    * Generate Go SDK.
    * Extract properties which are configurable in Azure portal (before running this workflow, screenshots of Azure portal containing targeted resource properties have to be added in `attachment/{resource}` directory).
* `schema`
    * Generate schema.
    * Generate property behaviors.
* `crud2BasicTest`
    * Generate CRUD methods.
    * Generate codes for resource identity.
* `basicTest`
    * Generate `Test{resource}_basic`.
    * Run and fix `Test{resource}_basic`.
* `otherTest`
    * Generate `Test{resource}_requiresImport`, `Test{resource}_complete`, and `Test{resource}_update`.
    * Run and fix `Test{resource}_complete`.
* `validateFunc`
    * Generate tests to identify invalid values for properties for validation function development purpose.
    * Configurations
        * `referenceTest`: Reference test used for generation. Should contain only the suffix after `_` in test name (for example, if `Test{resource}_basic` is used as reference, `basic` should be set).
* `maxItems`
    * Generate tests to identify maximum number of items for `TypeList` and `TypeSet` properties.
    * Configurations: `referenceTest`
* `forceNew`
    * Generate tests to identify properties which cannot be updated.
    * Configurations
        * `referenceTest`
        * `generatedTestPropety`: List of targeted properties in test. Generate tests for all relevant property if this is not specified.
* `planTimeCatch`
    * Generate tests to identify pair of properties which cannot coexist for plan time catch.
    * Configurations: `referenceTest`
* `runParallelTest`
    * Run parallel tests according to the number of HTTP proxies set in `nHttpProxy`.
    * Configurations
        * `testFileSuffix`: Suffix to identify the test files which the tests should be run.
        * `testRegex`: Regular expression to identify the tests to be run according to test names.
* `propertyName2ListResource`
    * Change property name according to `propertyNameMap` configuration if it is set. Key of `propertyNameMap` is initial property name while value is changed name.
    * Rearrange property according to `Required`, `Optional`, and alphabetical order.
    * Generate list resource.
    * Generate list resource test.
* `document`
    * Generate resource documentation.
    * Generate list resource documentation.
* `fixCommand`
    * Run compiler and linter.
    * Fix according to compiler and linter.
* `prContent`
    * Generate PR content.
* `flattenProperty`
    * Flatten properties listed in `flattenParentProperty` with child properties for one level.
* `property2Required`
    * Change properties listed in `requiredProperty` from `Optional` to `Required`.
* `customizeDiff`
    * Generate `CustomizeDiff` method.
* `bumpApiVersion`
    * Bump API version to the latest.
    * Configurations
        * `bBumpWithLocallyGeneratedSdk`: If set to `true`, latest API version of locally generated SDK is used. If set to `false`, latest API version of existing SDK in `terraform-provider-azurerm` is used.
