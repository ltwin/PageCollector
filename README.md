# PageCollector
A simple async page crawler
## How to use
* example1:

    You can simply run with no parameters

    ```bash
    python3 cli.py
    ```
    > When you run it this way,the program will read all of information from the configuration

* example2:

    This is a common way to use it

    ```bash
    python3 cli.py -i <input_path> -o <output_dir>
    ```
    > * The option `-i` means the file path that correspond to the list of sites to be crawled
    > * The option `-o` means the directory that save the crawl results

* More information:

    You can use the command

    ```bash
    python3 cli.py -h
    ```

* By the way,you can use the program with `splash` and `proxy pool`，when you add options `-S` and `-P`
## Distributed
You can start processes on multiple machines which is based on `dramatiq`.You can the submit some tasks to the crawler.Before using the crawler you need to install ` dramatiq `, and configured ` redis `
* **Caution**:
    
    To run the crawler, you need the necessary components
    * **MongoDB**: To save the crawler results
    * **Redis**: As a `dramatiq` message queue
* start:

    All commands are integrated into the file `command.py`
For starting some workers,you can run:
    ```bash
    python command.py start
    ```

    You can also specify the starting processes in current machine, which use:

    ```bash
    python command.py start -p 16
    ```
* submit:

    You can submit some tasks from cli or a source file
    
    Simple use:
    ```bash
    python command.py submit -u "http://www.example.com"
    ```
    From source file:
    ```bash
    python command.py submit -s "path/to/file"
    ```
    **Important**:
    
    You'd better specify the name of the crawler when submitting the task, otherwise the program will use the default name 'spider'
    
    Like this:
    ```bash
    python command.py -u "http://www.example.com" -N "spider_name"
    ```
    For more information, you can run:
    ```bash
    python command.py submit --help
    ```
* stop:

    If you want to stop the workers in current machine, you can use the `stop` command
    ```bash
    python command.py stop
    ```
    If it doesn't close properly, you can kill it
    ```bash
    python command.py kill
    ```
* export:
    
    Export the crawler results
    
    For example,you can export results to a file path
    ```bash
    python command.py export -t "http://www.example.com" -o "path/to/dir"
    ```
    For other uses, please refer to the help information
* help:
    
    Simply run command `python command.py --help`, you can get more information
