# Environmental based Screen and Keyboard
I've tried to rebuild the auto-mode from osx

# Install
- Simply start ;-)

# ACPI Support
To activate ACPI support edit the ```/etc/acpi/handler.sh``` and add the matching actions

## ACPI Actions
- lidopen
- lidclose

## Example
```bash
   button/lid)
        case "$3" in
            close)
                logger 'LID closed'
                xset -display :0 dpms force off
                /home/sammy8806/work/ebsk/ebsk.py --acpi=lidclose
                ;;
            open)
                logger 'LID opened'
                /home/sammy8806/work/ebsk/ebsk.py --acpi=lidopen
                ;;
    esac
    ;;
```

# License
(c) 2015 Steven Tappert
Licensed under the MIT/X Consortium License.
See [LICENSE](./LICENSE) for details.
