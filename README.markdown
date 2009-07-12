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
http://awesome.jakewharton.com for you to use. Should you want to host 
your own copy, though, a few simple steps are needed.

1.  Run `git clone git://github.com/JakeWharton/is_awesome.git`.
2.  Symlink a directory in your wwwroot to the `is_awesome` directory.
3.  Enter the `is_awesome` directory and run `git submodule init` 
    followed by `git submodule update`.

You should now have a working copy of the script in whatever directory 
you symlinked the `is_awesome` directory to.


Developed By
============
* Jake Wharton - <jakewharton@gmail.com>

Git repository located at http://github.com/JakeWharton/is_awesome/


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
