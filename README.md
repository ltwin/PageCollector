# PageCollector
A simple async page crawler
# How to use
* example1:
    <br>You can simply run with no parameters
    ```bash
    python3 page_collect.py
    ```
    > When you run is this way,the program will read all of information from the configuration
* example2:
    <br>This is a common way to use it
    ```bash
    python3 page_collect.py -i <input_path> -o <output_dir>
    ```
    > The option `-i` means the file path that correspond to the list of sites to be crawled
    > <br>The option `-o` means the directory that save the crawl results
* More information:
    <br>You can use the command
    ```bash
    python3 page_collect.py -h
    ```
* By the way,you can use the program with `splash` and `proxy pool`