About
=====
`is_awesome` is a small pyy-based python web application which 
automatically checks an encode's MediaInfo output for DXVA and Awesome 
compliance.

Since checking DXVA and the much more strict Awesome compliance involves 
up to 16 settings, this provides a much faster approach.

Compliance is indicated by either a green or red background for the DXVA 
and Awesome boxes which indicates compliance or non-compliance, 
respectively. The errors which were found are listed below along with 
which standard they apply against. Remember, anything DXVA applies to 
Awesome too.


Usage
=====
A up-to-date version of the master branch is always kept running at 
[awesome.jakewharton.com](http://awesome.jakewharton.com) for you to
use.

You can also POST data and receive a JSON or XML response at
[awesome.jakewharton.com/json/](http://awesome.jakewharton.com/json/) or
[awesome.jakewharton.com/xml/](http://awesome.jakewharton.com/xml/),
respectively.

Example JSON response:
    {
        "dxva": true,
        "awesome": false,
        "error_count": 1,
        "errors": "<ul><li><strong>Awesome: </strong><code>cabac</code> must be 1. Got: 2</li></ul>",
        "warning_count": 0,
        "warnings": "<ul></ul>"
    }

Example XML response:
    <?xml version="1.0" encoding="UTF-8"?>
    <compliant dxva="true" awesome="false">
        <errors count="1">
            <li><strong>Awesome: </strong><code>cabac</code> must be 1. Got: 2</li>
        </errors>
        <warnings count="0"/>
    </compliant>


Developed By
============
* Jake Wharton - <jakewharton@gmail.com>

Git repository located at
[github.com/JakeWharton/is_awesome/](http://github.com/JakeWharton/is_awesome/)


License
=======
    Copyright 2009 Jake Wharton

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
