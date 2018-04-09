# earlybird
Simple tools to implement delay-based metric for routing protocol on Linux:
measure one-way latency of tunnel, write out [bird](http://bird.network.cz/)
configuraions, and reload bird.

See also [Babel](https://www.irif.fr/~jch/software/babel/).

## Latency
Send UDPs that contain timestamps to caculate one-way latency between
two ends of tunnel. Require synced-time amongst ends (usually by ntp).

## Config template
The program doesn't implement any routing protocol. Instead, it only
write out config file that contains calculated delay-based metrics.
These configs can be loaded by other routing daemon, such as bird.

## Install & Usage
For Arch Linux user:
```bash
cd earlybird/package
makepkg
sudo pacman -U earlybird-git-<version>-any.pkg.tar.xz
```
Edit configs
```bash
cd /etc/earlybird
cp config_example.py config.py
vim config.py
```
Create a template
```bash
cp /etc/bird.conf templates/
vim templates/bird.conf
```
Start service
```bash
sudo systemctl start earlybird
```