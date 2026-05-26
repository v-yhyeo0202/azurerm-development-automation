import json
import os
import yaml

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

header = '''
// Copyright IBM Corp. 2014, 2025
// SPDX-License-Identifier: MPL-2.0
'''.strip()
service = dictConfig['path']['services'].split('/')[-1]

def generateEmptyRegistration():
    emptyRegistration = f'''
{header}

package {service}

import (
	"github.com/hashicorp/terraform-plugin-framework/action"
	"github.com/hashicorp/terraform-plugin-framework/ephemeral"
	"github.com/hashicorp/terraform-provider-azurerm/internal/sdk"
)

type Registration struct{{}}

var (
	_ sdk.TypedServiceRegistration     = Registration{{}}
    _ sdk.FrameworkServiceRegistration = Registration{{}}
)

func (r Registration) DataSources() []sdk.DataSource {{
	return []sdk.DataSource{{}}
}}

func (r Registration) Resources() []sdk.Resource {{
	return []sdk.Resource{{}}
}}

func (r Registration) Name() string {{
	return "{dictConfig['serviceName']}"
}}

func (r Registration) WebsiteCategories() []string {{
	return []string{{
		"{dictConfig['serviceName']}",
	}}
}}

func (r Registration) Actions() []func() action.Action {{
	return []func() action.Action{{}}
}}

func (r Registration) FrameworkResources() []sdk.FrameworkWrappedResource {{
	return []sdk.FrameworkWrappedResource{{}}
}}

func (r Registration) FrameworkDataSources() []sdk.FrameworkWrappedDataSource {{
	return []sdk.FrameworkWrappedDataSource{{}}
}}

func (r Registration) EphemeralResources() []func() ephemeral.EphemeralResource {{
	return []func() ephemeral.EphemeralResource{{}}
}}

func (r Registration) ListResources() []sdk.FrameworkListWrappedResource {{
	return []sdk.FrameworkListWrappedResource{{}}
}}
'''.strip()

    return emptyRegistration

def generateEmptyClient():
    emptyClient = f'''
{header}

package client

import (
	"github.com/hashicorp/terraform-provider-azurerm/internal/common"
)

type Client struct {{
}}

func NewClient(o *common.ClientOptions) (*Client, error) {{
	return &Client{{}}, nil
}}
'''.strip()

    return emptyClient

def generateSdkImport():
	sdkPackage = ''
	sdkPackagePath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'])

	with open(os.path.join(sdkPackagePath, 'PreGenerateSdkOutput.json')) as f:
		dictPreGenerateSdkOutput = json.load(f)

	if dictPreGenerateSdkOutput['sdkPackage']:
		sdkPackage = dictPreGenerateSdkOutput['sdkPackage']
	else:
		with open(os.path.join(sdkPackagePath, 'GenerateReplaceDirectiveOutput.json')) as f:
			sdkPackage = json.load(f)['sdkPackage']

	sdkImport = f'''
package {service}

import (
    "{sdkPackage}"
)
'''.strip()

	return sdkImport

def generateIndex():
	configPath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'indexConfig.json')

	if os.path.exists(configPath):
		with open(configPath) as f:
			dictIndexConfig = json.load(f)

		dictIndexConfig['index'] += 1
	else:
		dictIndexConfig = {
			'index': 0
		}

	with open(configPath, 'w') as f:
		json.dump(dictIndexConfig, f, indent = 4, ascii = False)

	return