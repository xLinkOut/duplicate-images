# Python Duplicate Images Finder
The goal is to find duplicate images via a beutiful web interface, where you can explore, select, move and delete single or a bunch of duplicate images from your computer.

Strong point of this software is [__pHash__](http://www.phash.org/): an open source software library that implements several perceptual hashing algorithms, and provides a C-like API. It ignores the image size and file size and instead creates a hash based on the pixels of the image. This allows you to find duplicate pictures that have been rotated, have changed metadata, and slightly edited.

This code is a full refactor of [this software](https://github.com/philipbl/duplicate-images), so thanks to @philipbl for the amazing work! :)

# Todo list
- [ ] Use a Virtual Environment that can be shared within the repository
- [ ] Use SQLite3 for the entire project to increase portabiliy
- [ ] Use Flask to create a beautiful, minimal and fast Web UI
- [ ] Write code as modular as possible
- [ ] Comment all the code
- [ ] Provide an accurate requirements.txt
- [ ] Provide multiple test's scripts
- [ ] Write a Wiki and a Quick Start guide
- [ ] Have fun!

## Note for personal reference
* When (at least) a duplicate is found, display only one with a "ribbon" element from Semantic UI with a counter of how many duplicates software found. 
* A click on "# Duplicates" display a modal where user can delete from local disk one or more duplicate images.
* In database save path and filename separately.
* Add path by drag and drop
