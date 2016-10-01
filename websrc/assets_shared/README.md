# Blender Web Assets
Blender Web Assets is a front-end framework which provides design and interactivity components for [Blender.org Websites](http://www.blender.org). You can see components in action on [the Boilerplate]( http://www.blender.org/wp-content/themes/bthree/assets_shared/utils/boilerplate.html).

## Install and usage
### Software you need
* **[GIT](http://git-scm.com)** To clone and contribute to this repository you need Git. Install from here: http://git-scm.com/downloads.
* **[SASS](http://sass-lang.com)** Our CSS preprocessor is SASS. If you don't have it installed, follow the step by step guide on their website: http://sass-lang.com/install.
* **[NODE.JS](http://nodejs.org)** We use Node.js to power Grunt wich will run repetitive tasks like prefixing CSS. Make sure, that you have Node.js installed on your system. Download from here: http://nodejs.org/download or install via a package manager: http://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager.

### Setup
1. Open up your terminal.
2. Clone this repository with `git clone git://git.blender.org/blender-web-assets.git`.
3. Navigate to this project using `cd /path/to/blender-web-assets`.
4. Do `npm install -g grunt-cli` to install the command line interface for Grunt (you maybe have to run this command as root).
5. Type `npm install` so all dependencies will be installed.
6. `grunt` will compile and prefix the SASS.

#### GNU/Linux Ubuntu Notes
* Ubuntu 13.10 and newer needs `nodejs-legacy` (or grunt won't output anything)
* Grunt needs `ruby-sass`

## Usage
Now you can type `grunt` in to the terminal every time you need the SASS compiled to css/generic.css. Isn't this awesome? Open the [index.html](index.html) in a modern webbrowser to review your changes.

## Authors
[Pablo Vazquez](http://developer.blender.org/p/venomgfx)  
[Niklas Ravnsborg-Gjertsen](http://developer.blender.org/p/niklasravnsborg)

## Copyright and license
This project is licensed under [the GPL license](LICENSE) copyright © 2014 Blender Foundation.
