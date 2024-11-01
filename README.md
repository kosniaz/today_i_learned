# Today I Learned: tutorials/memos/logs


## redirection confusion

Shell commands outputs can be redirected. E.g. 
```
cat a.txt > results.txt
```

redirects stdout to results.txt. However, we can also redirect stdout to stderr, e.g. 
```
cat a.txt 2>&1
```
The ampersand is there to distinguish from redirection to actual files named '1' or '2'. (in older versions 2>1 actually stderr redirected to stdout).

We can perform 2 redirections as we have two output streams:
```
diff a b 1>stdout_file 2>stderr_file
```

and what we can combine them (mind the order here)
```
diff a b 1>results_file 2>&1
```
If we set the reverse order in redirections, stderr will not be included in the file. To write both errors and standard output to file, the order should be like in the example. Standard output would first be redirected to the file, then stderr would additionally be redirected to the stdout handle that has already been changed to point at the file: command > file 2>&1. This is one more detail that shows C's influence on the Unix shells. 

Last, although not POSIX-standard, a quickie to combine stdout/stderr in one file is 
```
diff a b &> results_file
```

source: [wikipedia](https://en.wikipedia.org/wiki/Redirection_(computing)#Redirecting_to_and_from_the_standard_file_handles) and fooling around instead of preparing for interview.


## ping is not a valid "privilege escalation by setuid" example anymore

### Theoretical introduction

Unix files, apart from their permissions flags, also have their UID and GID flags.

In case of executable files, uid and gid flags specify
whether the resulting process has the uid and gid of the file owner
or the uid and gid of the user executing it. if uid (gid resp) is set to true
the process will have the uid (gid resp) of the file owner. This is how
some commands run by non-root users can have root priviliges: ping.

How are these flags represented? by another octal digit in front
of the three permissions octals. if setuid = 1, then we add 4
if setguid= 1 then we add two. So the two flags occupy the 2 highest
order bits in the bit triplet.

A classic example of that was ping.

### After a kernel release in 2011, ping has changed

As we can see in [this commit message](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?h=c319b4d76b9e583a5d88d6bf190e079c4e43213d), ping is now enabled in user-space. In other words, while `stat $(which ping)` gives us 0755 access modes, we can still use it without root priviliges.
Source:https://stackoverflow.com/questions/63177554/linux-why-am-i-able-to-use-ping-if-neither-setuid-nor-capabilities-are-set

## reminder: quotes in bash

```
[me@linuxbox me]$ echo text ~/*.txt {a,b} $(echo foo) $((2+2)) $USER
text /home/me/ls-output.txt a b foo 4 me
[me@linuxbox me]$ echo "text ~/*.txt {a,b} $(echo foo) $((2+2)) $USER"
text ~/*.txt {a,b} foo 4 me
[me@linuxbox me]$ echo 'text ~/*.txt {a,b} $(echo foo) $((2+2)) $USER'
text ~/*.txt {a,b} $(echo foo) $((2+2)) $USER
```

(example taken from [one of the oldest ebooks on the subject](https://www.linuxcommand.org/lc3_lts0080.php))

## difference between atomic read/write and atomic rwm

![image](https://github.com/user-attachments/assets/29dc0e4b-309a-4a2b-a3f9-57e44d3b06ea)

[Image source]https://preshing.com/20130618/atomic-vs-non-atomic-operations/)

[RWM](https://preshing.com/20150402/you-can-do-any-kind-of-atomic-read-modify-write-operation/) is more expensive than
[atomic read/store](https://preshing.com/20130618/atomic-vs-non-atomic-operations/)



## kaldi, pykaldi

Some lessons from my recent experience playing with [this repo](https://github.com/georgepar/kaldi-grpc-server):

1. No use copying python files into the container, if the files are already installed through `pip install .` in an earlier step.
2. Include the `poetry.lock` file to make dependency resolution faster.
3. uninstall everything you don't need as the last build step, to make the image as lightweight as possible.
4. Create a base image with all the necessary libraries/requirements etc, to make build time as quick as possible (as fast as copying some files and installing a couple extra libraries)
5. Ask the person who built the model if there are ivectors in the features.
6. kaldi uses beam search to build the transcription. For beam width `bw`, the time complexity of this operation is `O(bw^k)` where k is the maximum depth of the traversal.

## Mysql basics - pt2

How to add columns to an existing table

```
alter table calls_log add column error_level varchar(255)
```
How to remove columns from existing table
```
alter table calls_log drop column error_level

```

Allow null values in existing table
```
alter table calls_log alter column error_level varchar(25) NULL;
```
## Slowest way to add 10 seconds of trailing silence to bytes object
```
# suppose we have a bytes object, aka bytestring in audio_bytes
chunk_size= 6400 # suppose mono, 16000KHz sample rate, sample size is 2 bytes, and a chunk is 0.2 seconds 
extra_chunks = 10/0.2
extra_bytes_len = extra_chunks * chunk_size
for i in range(extra_bytes_len):
    audio_bytes+=b'0'
```
This will probably take more than 5 seconds, even a fast server takes around 15 seconds to do that.
The reason is that the bytes is immutable, thus a new object is created every time (that's a lot of mallocs!).

The right way to do that is to make a bytearray (which is mutable) and then join it with the bytes object.
```
trailing_silence_bytes=bytearray(extra_bytes_n)
audio_bytes= audio_bytes+trailing_silence_bytes
```


source: Experimentation, also [this](https://stackoverflow.com/questions/62903377/python3-bytes-vs-bytearray-and-converting-to-and-from-strings)


## Sysadmin stuff

### Testing UDP ports on a machine:

#### Happy case

server side:
```
$ nc -ulv 0.0.0.0 12345
Ncat: Version 7.70
Ncat: Listening on 0.0.0.0:12345
```

then open up client side:
```
$ nc -uv 10.10.1.2 12345
Ncat: Version 7.70
Ncat: Connected to 10.10.1.2:12345
```

the serve side is still like this:

```
$ nc -ulv 0.0.0.0 12345
Ncat: Version 7.70
Ncat: Listening on 0.0.0.0:12345
```
Then type in "abcd" and hit enter:

```
$ nc -uv 10.10.1.2 12345
Ncat: Version 7.70
Ncat: Connected to 10.10.1.2:12345
abcd
```
Then server gets the message
```
$ nc -ulv 0.0.0.0 12345
Ncat: Version 7.70
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.10.1.1.
abcd
```
#### Bad case 1: Port is already taken 

This one is purely on the server side. Run the server command, and if the port is already taken, you get this message:
```
$ nc -ulv 0.0.0.0 12345
Ncat: Version 7.70
Ncat: bind to 0.0.0.0:12345: Adress already in use. QUITTING
```

#### Bad case 2: In case firewall is blocking client -> server communication

Server will not display anything, client will get "Ncat: operation not permitted"
```
$ nc -uv 10.10.1.2 12345
Ncat: Version 7.70
Ncat: Connected to 10.10.1.2:12345
abcd
Ncat: Operation not permitted
```

#### Bad case 3: In case server side is down.

If you first kill the server then use the client (or just change the target port), you will get this behaviour:

```
$ nc -uv 10.10.1.2 12345
Ncat: Version 7.70
Ncat: Connected to 10.10.1.2:12345
abcd
Ncat: Connection Refused
```

Ncat: Connection from

## How to connect to mysql on localhost from a container

You can't use the socket that mysql clients do when you're running in a container (unless you mount it, but do you want to?).
Worry not, you just have to use the `127.0.0.1` instead of `localhost` and everything will be fine.

## How (not) to run a callcenter on opensips

https://github.com/OpenSIPS/opensips/issues/3123

## How (not) to make an alias to connect to a remote desktop on Win 10

1. Install putty (you'll understand why l8r)
2. create a folder to store aliases e.g. `C:\Users\kosniaz\Desktop\aliases`
3. add it to the path: search for "system variables" and make a new entry to the `PATH` variable:  `C:\Users\kosniaz\Desktop\aliases`
4. create a new batch file: connect.bat and open it with notepad++
5. write the following line: `putty <user>@<host> -pw <pass>` (source https://stackoverflow.com/questions/23419659/sshpass-is-not-recognized-on-windows)
6. Ready! Run `connect` on a new command prompt window.

## Pylinter and ALE/vim, part two

Watch out for virtual environments. You can debug pylint as follows:

:ALEInfo

this gives the output of the linter commands run (such as pylint). This is especially interesting to find out which pylint executable is 
run. E.g. in my case the following command was run:

```
['/usr/bin/zsh', '-c', 'cd ''/path/to/project/directory'' && ''/path/to/project/directory/venv/bin/pylint'' --output-format text --msg-template="{path}:{line}:{column}: {msg_id} ({symbol}) {msg}" --reports n --from-stdin ''/path/to/project/directory/python_file_i_opened.py'' < ''/tmp/vtD9kk2/1/python_file_i_opened.py''']
```

and I saw that it exited with `1`. 

Under ale, pylint runs as a separate process, and ale's python integration decides which one to run like this:

    First, it looks for a virtualenv, which is a directory called "virtualenv", "venv" or a couple of other options in the directory of the file being edited.
    If it doesn't find one, it moves up one directory and checks again, repeating this process on failure until it gets to the root.
    If it still hasn't found a virtualenv, it looks at the VIRTUAL_ENV environment variable and uses that.
    If that environment variable isn't set, it uses whatever first matches "pylint" (by default) in the PATH. 

If all the files you're editing use virtualenvs, and you're not doing something like editing files on an exported fileshare from a virtual machine running a different operating system, which unfortunately I do quite often, this works fine.

## The hierarchy of loggers in Python

`import logging` gives a singleton logger: that is the root logger. [TOOD: add the rest of this tip]


## Record and play audio in docker container (on linux host)

This worked for me
https://comp0016-team-24.github.io/dev/problem-solving/2020/10/30/passing-audio-into-docker.html

also used these lines to set the user at the end (after all the installation made as USER 0)
```
RUN useradd -rm -d /home/kosmas -s /bin/bash -g root -G sudo -u 1000 kosmas
USER 1000
```

## set correct shortcut to change keyboard layout

https://askubuntu.com/questions/1029588/18-04-ctrlshift-to-change-language

## use global packages in virtualenv

https://stackoverflow.com/a/53515591

## apt-get update “the following signatures couldn’t be verified because the public key is not available”

run 
```
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys <priv key>
```

https://chrisjean.com/fix-apt-get-update-the-following-signatures-couldnt-be-verified-because-the-public-key-is-not-available/

## search for text inside the packets in wireshark

To find a string within a packet, click on Edit > Find Packet. Under "Find By:" select "string" and enter your search string in the text entry box. You'll probably want to leave "Case sensitive" unchecked. Under "Search in", the default is "Packet list" but that will only find a string that appears in the Info column of the Packet List pane, which is the one-line-per-packet summary view. There is a lot more information in most packets than what appears in the packet list Info column, so try "Packet details" and "Packet bytes". 

[source](https://osqa-ask.wireshark.org/questions/4710/how-do-i-search-a-capture-for-a-string/)

## send test datagram udp
```
echo "This is my data" > /dev/udp/compute.ilsp.gr/5060
```

## Kill docker container from within


normally you can't kill PID 1 a docker container from the inside. But my mate gbastas did find this:
```
kill -INT 1
```

that was it.

## find out your ubuntu version and desktop
```
kosmas@kosmasbox:~$ echo $XDG_CURRENT_DESKTOP
ubuntu:GNOME
kosmas@kosmasbox:~$ lsb_release -a
No LSB modules are available.
Distributor ID:	Ubuntu
Description:	Ubuntu 18.04.6 LTS
Release:	18.04
Codename:	bionic
```

## shortest url of site for pinging

ping g.cn 

[source](https://www.gawker.com/318368/the-shortest-domain-name-ever)

## need to check on my burnout :/

## ubuntu freezing for 10-20 seconds 

So for some time, now and then, I had this weird issue. Out of the blue, my work linuxbox would not respond to anything for 10-20 seconds, apart from mouse movement (even tho clicking didn't change a thing). My first impression was that it was a memory or disk thing. Today it happened again. I saw that memory usage and hard disk capacity were OK (I was just 5 minutes after booting). At first I thought it was a firefox thing, as it happend when I was running firefox.  Switchd to chrome then. Then it happened agian.

At that point I searched a bit more, even though that meant losing precious time. I learned that in such cases, I can possibly reclaim control of the system by hitting alt and sysrq (print screen) + r. Tried, but that didn't work. Surprisingly alt-ctrl-F1 worked: I could logout and login to my user again, but all my GUI was still frozen even after that. What was the issue? I checked dmesg, nothing really interesting there. Just a silly error a number of times:
```
$ dmesg
...
usb_set_interface failed (-110)
usb_set_interface failed (-110)
usb_set_interface failed (-110)
...
```

When I googled it I found this weird result: [E-MU 0202 USB - freezes kernel / USB subsystem - kernel 4.15.15](https://bbs.archlinux.org/viewtopic.php?id=236356). Could this be it!? I checked my usb ports, and removed that weird webcam I had (unsuccessfully) tried to used some days ago. 
```
It was the webcam
```
This was no disk failure. It was the bloody Lamtech Webcam! After removal, I didn't have this problem again. I will try again to connect it, just to make sure my hypothesis is correct. I will update if something else pops up. 

## Help, my server is blocking my IP! (Or 'docker engine has limited subnets for its network pool')

By default, docker networks are created and assigned a subnet each.
The subnets created are drawn from the 172.17.0.0/16-172.31.0.0/16 subnet range, i.e.:
```
172.17.0.0/16
172.18.0.0/16
172.19.0.0/16
.
.
.
172.31.0.0/16
```

So we have 15 networks. What happens if we create more that 15? Docker starts drawing from another subnet pool:
192.168.0.0/20-192.168.240/20. That is
```
192.168.0.0/20
192.168.16.0/20
192.168.32.0/20
192.168.48.0/20
192.168.64.0/20
.
.
192.168.240.0/20
```

So here we have 16 more subnets available. What happens when we surpass this limit too? I don't know. I think there's more, although up to a point, you could have 31 automatically assigned-to-networks subnets.

Anyway, this post was started because a big frustration: until I make the first 15 networks, nothing bad happens. But when I mak e more, docker starts assigning them subnets from the 192.168.X.0 range, **my computer is ignored from the server's network**, because its VPN address happens to be in the 192.168.0.0/20 subnet too. 

In order to fix this, you have to, lamentably, delete the problematic docker network. Solution in steps:

### Step 1: Detect which docker network has stolen your IP:
```
ifconfig | grep -B 2 192.168
```
You will get something like this
```

br-20271d253c40: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.64.1  netmask 255.255.240.0  broadcast 192.168.79.255
--

br-23fa8842a863: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.16.1  netmask 255.255.240.0  broadcast 192.168.31.255
--

br-b22122a7fd66: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.0.1  netmask 255.255.240.0  broadcast 192.168.15.255
--
```
These are the bridge interfaces pertaining to each docker network. Taking into account that the broadcast address is the last address and the bridge address is the first in the network range, you can determine the IP range of every docker network. E.g. for the br-b22122a7fd66 interface, the corresponding docker network holds the range 192.168.0.1-192.168.15.255. 

### Step 2: delete said network (hopefully no one is using it anymore)

The corresponding network will be named like the string after the 'br-' prefix of its corresponding network interface. So, if we have an issue with
bridge 'br-b22122a7fd66', the docker network is named 'b22122a7fd66'. So it suffices to run
```
docker network rm b22122a7fd66
```
### Step 3: Make sure it doesn't happen again

How can we avoid this reccuring issue? The solution is to describe the subnets to be used in docker's `/etc/docker/daemon.json` file, as cited [here](https://www.lullabot.com/articles/fixing-docker-and-vpn-ip-address-conflicts) and [here](https://serverfault.com/questions/916941/configuring-docker-to-not-use-the-172-17-0-0-range/936255#936255). 

However, to do this, you need to delete all existing networks, stop all containers and restart the docker daemon.

## argparse: options vs positional parameters

the only difference is adding a double dash to the name. E.g.
```
parser.add_argument("csv", type=str, help="path to csv file") # positional 
parser.add_argument("--tts-host", type=str, help="tts server hostname") # option(al) 
```

## ripgrep "respects gitignore"

rg doesn't search in files ignored by gitignore. To avoid this, use ` --no-ignore`

## Ant Design pt.2 

Ant has loads of components, ready to use to make beautiful dashboards. It also provides a simple Row & Column layout to stack all your components. 
A good example is [this repo](https://github.com/Borja95/dashboardAntDesign) (source is [this youtube video-tutorial](https://www.youtube.com/watch?v=824rRS_bRYI)

After having created a basic layout for your components, you can make good use of ant by visiting its super detailed docs (with examples!), as in [this example here](https://ant.design/components/table/)

p.s. Reminder of padding and margin here https://blog.hubspot.com/website/css-margin-vs-padding
p.s.2 flexbox is nice too

## Ant Design and UMI

Ant design. 

I tried to learn this new ant design thing. But I had a problem. The [usage section](https://github.com/ant-design/ant-design-pro/#use-bash) starts with 

```
npm create umi
```

By the way, if you run  `npm init && npm create umi` fails complaining for the nonempty dir. Then I run `npm crete umi` and I get dependency issues. What the heck, I have nothing else installed there. However, it gets solved if I first `npm install create-umi` and I get lots of files in my directory. I check app.js and it is full of stuff I've never used before. Why is React JS so different everytime?

A sample of app.tsx
```
kpalios@dialoque3:~/workspace/planv/planvt$ cat src/app.tsx                                                                                                    [67/662]
import type { Settings as LayoutSettings } from '@ant-design/pro-layout';                                                                                              
import { SettingDrawer } from '@ant-design/pro-layout';                                                                                                                
import { PageLoading } from '@ant-design/pro-layout';                                                                                                                  
import type { RunTimeLayoutConfig } from 'umi';                                                                                                                        
import { history, Link } from 'umi';                                                                                                                                   
import RightContent from '@/components/RightContent';                                                                                                                  
import Footer from '@/components/Footer';                                                                                                                              
import { currentUser as queryCurrentUser } from './services/ant-design-pro/api';                                                                                       
import { BookOutlined, LinkOutlined } from '@ant-design/icons';                                                                                                        
import defaultSettings from '../config/defaultSettings';                                                                                                               
                                                                                                                                                                       
const isDev = process.env.NODE_ENV === 'development';                                                                                                                  
const loginPath = '/user/login';                                                                                                                                       
                                                                                                                                                                       
/** 获取用户信息比较慢的时候会展示一个 loading */                                                                                                                      
export const initialStateConfig = {                                                                                                                                    
  loading: <PageLoading />,                                                                                                                                            
};                                                                                                                                                                     
                                                                                                                                                                       
/**                                                                                                                                                                    
 * @see  https://umijs.org/zh-CN/plugins/plugin-initial-state                                                                                                          
 * */                                                                                                                                                                  
export async function getInitialState(): Promise<{                                                                                                                     
  settings?: Partial<LayoutSettings>;                                                                                                                                  
  currentUser?: API.CurrentUser;                                                                                                                                       
  loading?: boolean;                                                                                                                                                   
  fetchUserInfo?: () => Promise<API.CurrentUser | undefined>;
}> {            
  const fetchUserInfo = async () => {
    try {                                                              
      const msg = await queryCurrentUser();
      return msg.data;               
    } catch (error) {
      history.push(loginPath);         
    }                       
    return undefined;                
  };              
  // 如果不是登录页面，执行
  if (history.location.pathname !== loginPath) {
    const currentUser = await fetchUserInfo();
    return {
      fetchUserInfo,
            currentUser,
      settings: defaultSettings,
    };
  }
  return {
    fetchUserInfo,
    settings: defaultSettings,
  };
}
```

Then I compared this initial project to the other ant design projects in youtube video tutorials, but there was no sign of any weird typescript whatsoever.

Then I realized that 
```
antd is a library
```
and 
```
umi is an entire framework
```

### The umi framework

This is a completely independent thing, but coincidentally made by the same people who made ant. They have a [cute logo though](https://umijs.org/)


## A minimalist Vim plugin manager

Named vim-plug. [Very easy usage](https://github.com/junegunn/vim-plug)

I used it to install typescript syntax plugins. [source](https://thoughtbot.com/blog/modern-typescript-and-react-development-in-vim)




## Pull requests

For a pull request, you:

 * Fork the repo (this will create a repo of your own)
 * In your copy of the repo, make changes in a certain branch (and commit them)
 * Don't forget to add the public repo as a remote, so that you can stay up to date with the latest changes. `git add remote upstream https://github.com/user/repo.git`
 * Create the pull request using the github page (preferably do it early and with the WIP tag in the title)
 * Write a good PR message (use the correct tags)
 * Accept comments, corrections etc and correct the code

## HashMap and custom classes.

I had a strange bug in a `PriorityQueue` I didn't implement (but I had to write unit tests for).
At some point I concluded that it was somehow related to a `HashMap` that was being used to keep track of the positions of every element in the tree: the reverse search used in `pq.decreasePriority(node,new_priority)` for some reason failed.
But why? I realized that it was because the HashMap wasn't working well with the data I was passing. It was actually overwriting everything to the same pair! That's how I realized (== googled and found out, link [here](https://dzone.com/articles/things-to-keep-in-mind-while-using-custom-classes)) that *it was calculating the same hash for all the different elements I passed.* The reason was that I was hashing a subclass that had only one extra field (adding to the inherited ones) and that I was creating new elements with the same value in that field, (even though the inherited fields had different values). To sum up, make sure to experiment with how a custom class is hashed in a `HashMap`
Additional points to consider
* Changing a field of an element changes its hash value. Therefore, it is treated as a new insertion by the `HashMap`
* Normally you shouldn't unit test private methods.
* Using toString on an object that doesn't define it just returns 1.


## Kubernetes terminology

* **Kubernetes deployment configuration**: the yaml file with all the stuff
* A **cluster** has **nodes**. A **node** has **pods**. **Pods** have **containers**. You can do stuff 
  with the containers, using **kubectl**.
* **kubectl** is your go-to tool for doing anything kube-related.
* If you have a pode with just one container, 
  `kubectl exec <podname> command` runs a command in that container.
  Works the same way as `docker exec <container-id>` command.

## Docker games, pt.1

It's weird, but today my [rasa](rasa.com) container wasn't behaving as expected. It was supposed to train the model 
for our latest voice assistant version, to be deployed and tested in [gitlab's CI/CD pipeline](https://docs.gitlab.com/ee/ci/quick_start/) of our repo. To train the model we always use the latest version of rasa's image, but this time something went wrong, there was a permission issue. More specifically, the running container couldn't write in the directory that was used to mount a host directory. I said, WTF. Why? On my host system, I navigated to the mapped directory, and double-checked the ownership of the directory. It was, as always the same, my host user, id 1000. On the other hand, docker images have always run as root in my system (because, as specified [here](https://medium.com/redbubble/running-a-docker-container-as-a-non-root-user-7d2e00f8ee15), root is the same uid in all unices). Could it have changed? Am I just too tired for this s\*\*t ? How can I know the user running in the docker container? 

Turns out I can't enter the container's shell, because it has no shell, only a specfic set of commands (train, run, actions etc). I tried running alpine's shell with the same parameters, and I created a file on the mounted dir. The result was a root owned file. Ok, so the weird user thing must be image specific. So what to do then?

                       **Make the folder writable by everyone**

Yes, that worked. By the way, when the model was created and stored in the host-system dir, I saw that the owner was some person with uid 1001 who belonged to the root group, 90% percent a rasa thing. 

P.S. In the end, I used an older version, because of incompatibility with the one used in running the bot. The older version behaved as expected: file ownership was root again.


## First k messages were not received by tcp socket server

So yes, I was writing a simple client-server app in C, and I was using the humble sys/socket library. I had created a very basic protocol, where a client would first send a message declaring its options (much like a urlencoded parameter list) and then would send a number of messages, each message corresponding to one piece of data to be stored in a database. This was something that I had previously used with websockets, where message was handled by an `on_message()` method.

So I happily wrote some unsafe C to see the thing working, without having put much thought to it. I would apply the usual checks afterwards (e.g. error checking). However, when I executed the code, I realized something weird. Sometimes, the server missed a number of messages, specifically the first `k` ones, where k ranged from 1 to, say, 20. I thought something was wrong with my application, I even used my trusty tcpdump command to check if everything was sent correctly, and it was!
But still, it wasn't read correctly by my simple read loop inside the server code.

Debugging was made even more difficult by the fact that I could not print out messages to the terminal because the server code was serving each client in a separate process. So I first learned an efficient way to print messages from a forked process. 
*The trick was to write to a debug file and use fflush() all the time so that the file was actually written to. 
Without fflush() I wouldn't have got anywhere because the forked process would stop with
an error caused by the client process ending ("socket closed" error) and therefore would not flush the buffer.*

With my newly acquired printing skills, I made the server print whatever it read from the socket. And I found that the read() 
method was not fired whenever a tcp packet was received. Rather it was trying to buffer incoming messages, and then it read many messages at once. Which was nearly okay, as I was actually concatenating the incoming messages until the very end, when I would move on to the processing. But there was a bug there. The initial message was parsed in such a way that didn't look at the entirety of the message, but only at the options of interest to the server (which actually only cared about 2-3 values, namely an opcode and some metadata). Therefore, any trailing content was ignored, which was an issue because the intial message was not read "by itself", but accompanied by a number of messages sent at later times (because of the buffering mechanism explained in the beginning of this paragraph). Ooops! 

My fix was of course to store the part of the read string that was *after* the intial message. 

# WebAudio problems

* adding a new module from file: First I had a cors issue -> started up a simple http server. Then I had a network error (dafuk?). Turns out that network error sometimes is a "module not found" error - I had simply mistyped `process.js`!

# Twilio `<Connect>`

At work we have a Voice Assistant service that works with websockets. The client connects to the socket, and when ready to speak, 
send a "RESTART_COMMUNICATION" message, followed by base64 audio chunks. (that is, the user's real time voice audio). When the server recognizes a full phrase, it send back a signal to tell the client to stop sending audio chunks, and after some 300ms, the client receives an mp3 with the VA's response. 

To make that work with twilio, one has to:

* write a client that keeps a bidirectional channel with the phone call - through which it exchanges some json info - while keeping an open socket with the VA service.


# Today 14-9-20 i lrnd

1. rename your tmux sessions according to project: `Ctrl-B` & `$`
2. if you have `CMD` specified in Dockerfile, use docker-compose build to update the cmd
3. To check if a websocket is working, use your browser as js interpreter: f12-> Debug (or console) and run
```
ws = new WebSocket(<endpoint>)
```

# Acer inspire: got locked out of bios

Quick response: just get the reset key from [here](https://www.biosbug.com/acer-10-digit/)

# Install Linux alongside an existing Win10 partition.

1. Resize the Win10 partition.
2. Create a Linux Swap partition around the size of your RAM
3. Create a Linux ext4 partition for the root of your Linux, perhaps an extra one for the home folder, if deemed necessary.
4. Configure the installation: install grub in the existing ESP partition, select the swap partition for swap, set the home and root partitions
5. Hit install
6. Boot into windows, add the grub menu to the boot menu and set it first in the list. Use the command 
```
bcdedit /set {bootmgr} path \EFI\<YOUR_DISTRO>\grubx64.efi 
```
7. If it doesn't work, boot into Linux and use 
```
sudo efibootmgr
```
To see what GRUB sees as legit boot options. 
8. If step 6 doesn't work, you may need a temporary solution. Try setting 
```
sudo efibootmgr -n 000X
```
where X is the number of the linux option in the output of the `sudo efibootmgr` command.

# Basic Python syntax:

When you see something like 
```
    def __call__(self, string, univ_pos, morphology=None):
        if not self.rules:
            return [self.lookup_table.get(string, string)]
        if univ_pos in (NOUN, 'NOUN', 'noun'):
            univ_pos = 'noun'
        elif univ_pos in (VERB, 'VERB', 'verb'):
            univ_pos = 'verb'
        elif univ_pos in (ADJ, 'ADJ', 'adj'):
            univ_pos = 'adj'
        elif univ_pos in (PUNCT, 'PUNCT', 'punct'):
            univ_pos = 'punct'
        else:
            return list(set([string.lower()]))
        lemmas = lemmatize(string, self.index.get(univ_pos, {}),
                           self.exc.get(univ_pos, {}),
                           self.rules.get(univ_pos, []))
        return lemmas
```

You might wonder what is this getter?  Well it is python's suggested way of getting stuff from dicts, and the second argument is just the return value in case the 
entered key was not found. 

# Docker-compose build taking forever

There is something called `build context`. This is the folder where the dockerfile is built from. This doesn't have to be the folder the Dockerfile is stored.
Every file that is referenced inside the Dockerfile must be inside the context folder. This is why a container that need files across the whole project normally should have the project root as its `build context`. 

Before building a new image, docker needs to store the whole context in a special place. In some cases, where the context is unusually large, this can take forever. And the worst of all is that docker-compose does not give any output on this. On the contrary, `docker build` does: it counts the megabytes as they are copied from the context. Use docker build if you want to see if the context is too big; then reduce it to make docker-compose build responsive again.

# Change project name willingly in docker-compose

Normally project name for docker-compose is by default the name of the enclosing dir. This can cause problems if 2 dirs have the same name in your system.
To deliberately set a project name, use `.env` in the same dir as your compose file:
```
COMPOSE_PROJECT_NAME=YOUR_PROJECT_NAME_HERE
```
# Some useful search and replace:

## Case 1: extend logging with writing to a file too:
```
:%s/logging.info(\(\_.\{-}\))/logging.info(\1)^M    self\.temp_file\.write(\1)
```
## Case 2: wrong format in the yaml for rasa's automated test stories
correct format:
```
 - user: |
     Χελλου
   intent: Greetings
```
Current format:
```
  - intent: Greetings
    - user: 
      Χελλου
```
Steps to solve:
1. `:%s/    - user:/  - user:/g`
2. `:%s/  - \(intent: \_.\{-}\)\n  \(- user:\_.\{-}\n\_.\{-}\)/  \2\r  \1/g`
3. Clean up

# Displaying unicode characters from their hex representation using json!

Very commonly, rasa's report files are fiddled with codepoints in the `\u` notation (e.g '\u039e\u03ad\u03c1\u03b5\u03b9\u03c2').
This can be fixed in various ways, e.g using a conversion site. However this is not good. So I wrote this script:
```
# display_json_in_unicode.py
import json
import sys
INPUT_F= sys.argv[1] if len(sys.argv) > 1  else "input.json"
OUTPUT_F= sys.argv[2] if len(sys.argv)> 2 else "output.json"
with open(INPUT_F,"r") as f:
  dic= json.load(f)

with open(OUTPUT_F,"w") as ww:
  json.dump(dic,ww,ensure_ascii=False,indent=4)

```

You can use it like this:
```
python3  display_json_in_unicode.py in.json out.json
```

# one line https server

```
openssl s_server -accept 7781 -cert server.cert -key server.key -WWW
```

# argparse basic modes

```
#pass
```

# Using GPU's (nvidia)
```
# make all GPUs invisible
export CUDA_VISIBLE_DEVICES='' #https://developer.nvidia.com/blog/cuda-pro-tip-control-gpu-visibility-cuda_visible_devices/
```

# change remote url of submodule
```
git config -file=.gitmodules gitmodule.NAME.url <url>
...
```
[Read the source](https://dev.to/serhatteker/changing-git-submodule-repository-to-other-url-branch-356p)

# pruning old docker images

```
docker image prune -a --force --filter "until=2020-01-12T00:00:00"
```
or if you want to filter based on age, e.g. 24h, 10d or 1 year, use the h to specify hours
```
docker image prune -a --force --filter "2400h" # 100 days
```

# Run any one of the following command on Linux to see open ports
```
sudo lsof -i -P -n | grep LISTEN
sudo netstat -tulpn | grep LISTEN
sudo ss -tulpn | grep LISTEN
sudo lsof -i:22 ## see a specific port such as 22 ##
sudo nmap -sTU -O IP-address-Here
```

# CORS: acceptance of your HTTP request is not just one header away

as seen here, your http server must handle "preflight" too https://stackoverflow.com/questions/35254742/tornado-server-enable-cors-requests

# Maven

What is maven and why is it useful? ---> [check this](https://www.youtube.com/watch?v=bSaBmXFym30)

# Python CrossPlatform IO

Welcome to cross-platform issues. Issue 1:

## Unicode error while reading from file:

When reading non ascii characters, windows' python will fail when reading:
```
  File "c:\dist\python\lib\configparser.py", line 763, in readfp
    self.read_file(fp, source=filename)
  File "c:\dist\python\lib\configparser.py", line 718, in read_file
    self._read(f, source)
  File "c:\dist\python\lib\configparser.py", line 1015, in _read
    for lineno, line in enumerate(fp, start=1):
  File "c:\dist\python\lib\codecs.py", line 321, in decode
    (result, consumed) = self._buffer_decode(data, self.errors, final)
  File "c:\dist\python\lib\encodings\utf_8_sig.py", line 69, in _buffer_decode
    return codecs.utf_8_decode(input, errors, final)
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte
```

As a bonus, you can use [this site](https://pages.cs.wisc.edu/~markm/ascii.html) to find if something is ascii.

Anyway, to fix this issue, you must open the file in utf-8 mode like this:
```
f = open("test", mode="r", encoding="utf-8")
```

Same applies for opening file to write it.

# Machine inaccessible through VPN 

For some reason, we had a server here at work which at some point didn't respond to any requests coming from the VPN. Server was unreachable, `ping`s, `ssh`s, `curl`s, everything just timed out. At that time I had lots of things on my hands so I just switched to a "backup" VPN we had, and it worked. However, others tried to access it through the main VPN, and couldn't. When I found some time, I tested some of my hypotheses:

* It wasn't a wrong setting on the client side.
* No, it wasn't DNS
* Iptables didn't block any incoming traffic
* Yes, it was reachable inside the workplace LAN
* Yes, I could just work around the problem by using another server as a middleman/woman/person.

But what was it? I send a message to our netadmin, initially he was at a loss. The next day I saw a message on MSTeams:
```
You have assigned 192.168.10.0/24 to the docker network, i.e. the bridge interface is received all traffic 
from this subnet. This includes all addresses in our VPN.
```

Daym. When did I do that? Why? I wouldn't have done this intentionally, ever. 
I searched for this subnet in the interfaces of the server. I ran `ifconfig | grep -C 2 192.168`
```
br-7d0750ee4e98: flags=4099<UP,BROADCAST,MULTICAST>  mtu 1500
        inet 192.168.0.1  netmask 255.255.240.0  broadcast 192.168.15.255
        ether 02:42:00:d8:82:d8  txqueuelen 0  (Ethernet)                 
        RX packets 0  bytes 0 (0.0 B)                             
--                                   
                                                             
br-c76612a469fb: flags=4099<UP,BROADCAST,MULTICAST>  mtu 1500             
        inet 192.168.48.1  netmask 255.255.240.0  broadcast 192.168.63.255
        ether 02:42:8e:98:da:0a  txqueuelen 0  (Ethernet)                     
        RX packets 0  bytes 0 (0.0 B)                                   
--                                                          
                                                                  
br-f50000b10b5d: flags=4099<UP,BROADCAST,MULTICAST>  mtu 1500            
        inet 192.168.32.1  netmask 255.255.240.0  broadcast 192.168.47.255
        ether 02:42:01:de:83:af  txqueuelen 0  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)                             
--     
```

Three bridges were using this subnet. However I had no time to search for stuff, so I just deleted the unused networks.
```
docker network prune
```

But now I will never find why I had these networks in the first place. 

# install python linter on vim real quick (if vim version > 8)

1. Install ALE just by cloning repo to vim modules folder (like [this](https://github.com/dense-analysis/ale#standard-installation))
2. Install pylint through pip

# Fast API is actually super fast for http

# Install tmux resurrect  

1. Install tmux plugin manager https://github.com/tmux-plugins/tpm (check README.md)
2. Install tmux ressurect https://github.com/tmux-plugins/tmux-resurrect (check README.md)
3. Install tmux continuum if you want autosave, autoload https://github.com/tmux-plugins/tmux-continuum (check README.md)
4. Set storing pane contents https://github.com/tmux-plugins/tmux-resurrect/blob/master/docs/restoring_pane_contents.md

While tehse tmux plugins are nice, they will not store command history per pane.

## Bonus, setting max scroll buffer, and clearing it (using key bindings)

To set max scroll buffer in tmux, add this line to `~/.tmux.conf`
```
set -g history-limit 15000
```

To map clearing the history to Ctrl-k, add this line to `~/.tmux.conf`
```
bind -n C-k send-keys -R \; send-keys C-l \; clear-history
```

*Attention:* Even after you delete this line and reload the configuration (with Ctrl-b and then I) this binding will persist. If you want to undo this setting you will have to go out your way as [here is no easy way to set the key chord back to its previous value](https://unix.stackexchange.com/questions/57641/reload-of-tmux-config-not-unbinding-keys-bind-key-is-cumulative)

In any case, my current tmux config is the following:
```
# List of plugins
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-sensible'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'
# store the pane contents on save
set -g @resurrect-capture-pane-contents 'on'
# restore last saved environment on tmux restart
set -g @continuum-restore 'on'
# set buffer history to 15000 so as to preserve disk space
set -g history-limit 15000
# set ctrl-k to clear the pane buffer, if you dont want it anymore
bind -n C-k send-keys -R \; send-keys C-l \; clear-history

# Initialize TMUX plugin manager (keep this line at the very bottom of tmux.conf)
run '~/.tmux/plugins/tpm/tpm'
```

# Python timestamps.

So you have a fastapi server, and need to close connections after n seconds of inactivity. 
An easy way to do it, without add callbacks, timers etc is to check if a connection has expired every time a new one needs to open.
That way, you can ensure that expired connections release their resources before the next time they are needed.

## Datetime (or timedate?) and timedelta. How I remember it

I always forget how the classes are named. My guess is that the names are like this:

```
import datetime.datetime as dt
import datetime.timedelta as td
print("Current time is {}".format(str(dt.now()))
saved_ts= dt.now()
await sleep(2)
max_conn_time = td(seconds=30)
elapsed_time = dt.now() - saved_ts
print("Elapsed time is {}.format(str(elapsed_time)
if elapsed_time > max_conn_time:
    print("too much time has passed, shutting down")
    
```

## How datetime/timedata cirrect syntax

```
import time
# import the class definitions
from datetime import datetime as dt
from datetime import timedelta as td

# create the objects
then = dt.now()
time.sleep(2)
now = dt.now()
max_allowd_diff= td(0,1,400) # 10 seconds
if ((now-then)> max_allowd_diff):
    print("Diff is too long")
else:
    print("okay, time is not too much")
print(now-then)
```

# clean up tmp from dem rasa files
use the find command. First go inside `tmp`.
```
find . -maxdepth 1 -type d -name 'tmp*' 
```
Inspect the results of this command. If they are correct, delete them with the next cmd 
(**WARNING, MAKE SURE YOU DON'T DELETE SOMETHING USEFUL**)
```
rm -r `find . -maxdepth 1 -type d -name 'tmp*'`
```
# Add new partition to lvm 

Follow this guide for ubuntu:

https://www.cyberciti.biz/faq/howto-add-disk-to-lvm-volume-on-linux-to-increase-size-of-pool/

# garbled characters in vim driving you crazy 

Check your .vimrc, there's a change youve forgotten to add:
```
set encoding=utf-8
scriptencoding utf-8
```
# Python passes by sharing

that means that objects are passed by value if they are immutable, (e.g. integers, strings)
and by reference if they are mutable (e.g. lists, dicts)

reference: [this SO answer](https://stackoverflow.com/a/15078615)

# Rasa X Api JWT Bearer token authentication

## Step one: get the actual token (not the one in the environment of rasa x). Source [here](https://forum.rasa.com/t/using-the-http-api-how-to-get-bearer-token-programmatically/10256)
```
curl -XPOST http://localhost:5002/api/auth -d '{"username": "me", "password": <PW>}'
```
This will return a token, which you will store in a file and then put inside a env variable
```
TOKEN=`cat token.txt`
```
## Step two: use the token (correctly!)
```
curl -H "Authentication: Bearer $TOKEN" http://localhost:5002/api/health
```
**don't forget the api part!** Otherwise you will get html responses.

# Refactoring the wizard web client

## Adding authentication

This was supposed to be easy. I just need an initial form which would activate a javascript function to forward the inserted password to a simple server endpoint waiting on the backend. For that, I would have to make a POST request with the pass in the message body, so as to be encrypted. Then the server will respond would have to respond with a cookie, which then is used in the websocket url, otherwise the connection would be dropped. 

My problem was, I couldn't make the POST request pass through. I followed [this tutorial](https://www.freecodecamp.org/news/here-is-the-most-popular-ways-to-make-an-http-request-in-javascript-954ce8c95aaa/), which didn't work well for me. Maybe it was pure chance, but [the official mozilla one got it much better](https://developer.mozilla.org/en-US/docs/Web/API/fetch).

Anyway, the new code was pretty straightforward: I added a new function which run the `fetch` library's methods to perform an `HTTP POST` request, and I set the promise's target to be the function that had the rest of my code. However, the client failed with NetworkError (kind like [this one here](https://github.com/github/fetch/issues/310). After googling it, I found out that it was probably the same old CORS error that I have with the FastAPI servers now n then.

### A debug tool for CORS errors:

Use [this site](https://www.test-cors.org/) to test server response to the preflight (OPTIONS) message. After some trouble using it, I made it work, and I found out there was nothing wrong with my server's CORS. What was it then?

```
Due to the behaviour of form-submit, the client was POSTing the password, but it was killing the page right afterwards (by refreshing it).
```

To fix that, I had to set the action to be `#` and to return false after calling the onSubmit method, as described [here](https://stackoverflow.com/a/57226770)

## Improving the looks with a CSS template.

In the beginning I looked around for a template, but it didn't work because I wasn't importing it correctly. It must be
```
<link rel="stylesheet" href="my_css.css">
```
### Don't use Bootstrap css for vanilla html/css/js duh

Then it worked, but darn, it was a Bootstrap css. [It was working in js-fiddle](https://jsfiddle.net/cy8hro26/), so I had thought it would be okay in my own implementation. It kinda worked, but it had some issues. First all the elements were in the left, not in the center, as I wanted them.
Luckily I was able to fix it by using `text-align: center`, as well as using [this trick](http://jsfiddle.net/3F5WQ/4/) to align the buttons in the same row. 
The pushed code is [here]() (you need to be in the repo to see it, :/)

# Python Remove from list
```
my_list=[1,2,9]
my_list.remove(9) # now my_list=[1,2]
```
# Change project name in docker compose, or you'll have conflicts

Project name in docker compose is by default the containing folder 
```
(but what if your compose file is in the root dir?)
```
Sorry, an intrusive thought. Where was I... Ah yes. So the project name is what your network, your images and your containers and named after. E.g, the network will be named `parentDir_default` and a service named `asr` will have its image named `parentDir_asr` and its container named `parentDir_asr_1`.
Of course, you can change these names by adding your own external network, and change the suffix of the service's image/container names by editing the `container_name` and `image` fields of every service separetely. 

Unless you specify a different project name, which is a much simpler option. That means that images and containers will keep the suffix used in the compose file, but the prefix will change. This can be achieved as follows:
```
docker-compose -p myProject build
```
and
```
docker-compose -p myProject up
```

Even better, to the `COMPOSE_PROJECT_NAME` variable in `.env`. 

source https://github.com/docker/compose/issues/2982

# When something that was supposed to be working breaks....

This happens to me all the time. Ι believe something is working, something I take for granted, but damn!
Turns out didn't code/commit/deploy it well enough.

Then I realize I either have to stop what I'm doing and fix it (and therefore lose time and focus)
or continue what I'm doing and ignore the protests of everyone affected by the break. 
```
This is damn stressful
```
But the thing is, that's what happens when you make software without proper testing, and deployment. 
Also this happens when everything is working in test deployments, not in proper ones. What's more, 
to complete something takes more than to see it work. We should emphasize more on all the things 
that are needed **after** something is done. 

But in the meantime, bugs happen all the time, and even when it's not our fault, it's our resposibility.
In other words, it's our job, and our job shouldn't be an emotional rollercoaster. We should have some time reserved for the occasional 
urgent bug, some mistake in deployment, some 1 hour quick fix that needs to be done. It's part of the deal. 
```
Software is complex by nature, so it's a wild beast to tame.
```
Don't be overwhelmed when it kicks and breaks ocassionally. Relax and enjoy the problem solving that ensues :)

# Unicode file names giberrish when downloading entire folder from OneDrive

Turns out this is a bug when downloading from Linux. (Or an evil MS trick)
After trying to decipher the weird code (which was displayed on octal on the linux server) I fired up my windows machine
and downloaded the files from the browser and voila! The filenames were now readable, so I uploaded them to my server and 
everything was fine:
```
scp -r folder_with_greek_names kosmas@myserver:~
```

# Change python imported code
Something simple that I hadn't realized.

When working with python, you can modify the source of the libraries you are using. They are normally stored in `path/to/venv/lib/python3.7/site-packages/`. Use rg and/or find to see what you want to modify or override in your own implementation.

# Rasa actions server issues

Today I was working on adding a user story on Theano, our covid va chatbot. All I had to do was to override the `validate()` method, which was called once per turn while chatbot is in executing a form. The aim was to add handling of a special case in forms where the user could ask for location-specific data: sometimes user asked for city-specific data. First I had to find the correct version of validate to modify. Normally, I would have searched in the repo of `rasa-sdk`. But as my current version was not in any of the repo tags, I couldn't just go find the exact version of validate running. Then I realized that all rasa code resides in my `venv/lib/site-packages` directory. So all I had to do was run `rg "def validate(" path/to/my/venv` and to find the file where validate is defined. 

After I spent some time just to realize my code is available freely at my venv, I had to do the job inside the function, and then it would be over. However, as brief_country was a pre-filled slot, `validate()` was run twice (as pointed out [on the forum](https://forum.rasa.com/t/slots-get-filled-twice-in-formaction/13660/8), validate is run twice in the begging of the form, if there is a prefilled slot). Aaaand there I had another iteration on trying to solve this thing. Ideas were:

1) check the tracker for past actions, and dont utter the desired message if validation action has already run this dialogue turn
2) set a slot to count if validation has been run again this turn
3) check utterances object, in case it holds everything not uttered yet


Some 3 hours later, none of those worked. Reason was that the tracker object wasn't updated with the form actions, probably because they all belonged to the rule/form policy. All the tracker knows is that the `covid_statistics_form` is run.

So I ended up using a global dict of `{client_id : last_turn_where_validation_was_run}`

# setting up kubernetes for Theano pt1


### Questions 

1. which kubernetes distro to use? e.g. minikube, k3s, microk8s, kind (good with docker images!)
2. tutorials? Found some, see next section. i) 
4. to helm chart or not to helm chart?

### Tutorials

1. [ ] Some guy's simple hands-on tutorial https://testdriven.io/blog/running-flask-on-kubernetes/ 
2. [ ] Offical on services https://kubernetes.io/docs/concepts/services-networking/service/
3. [ ] Official on deployemnts https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
4. [ ] Official on Workloads
5. [ ] Rasa setup kuber
6. [ ] More on helm https://jfrog.com/blog/10-helm-tutorials-to-start-your-kubernetes-journey/`

### Have read

1. https://stackoverflow.com/questions/60991658/kubectl-what-does-client-vs-server


# Setting up k8s for theano pt2

With kubespray and vagrant. Steps 

1. install vagrant, libvirt, qemu, kvm, etc
    - https://joachim8675309.medium.com/devops-box-vagrant-with-kvm-d7344e79322c
2. Add $USER to groups: libvirt, kvm
3. pull kubespray repo from github (in `~/workspace/k8s/`)
4. `pip install -r requirements.txt` (of kubespray repo)
5. edit Vagrantfile (or create separate config file) for desired VM characteristics
    - 6 total nodes (each node has 6 vCPUs, 32GB RAM)
    - 2 master nodes
    - 3 etcd nodes
6. `vagrant up` (creates and configures all the VMs and the kubernetes cluster)
7. Install kubectl: `sudo snap install kubectl --classic`
8. copy `admin.conf` (created in inventory/sample/artifacts/ ) to `~/.kube/config`
9. Deploy Dashboard UI
    - https://www.replex.io/blog/how-to-install-access-and-add-heapster-metrics-to-the-kubernetes-dashboard
    - to access dashboard OUT of localhost, reverse ssh tunnel is necessary:
        - `ssh -N -f -L localhost:8001:localhost:8001 kubaras@chomsky`

# setup disk 

1. use fdisk to partition full disk in ext4
2. mount in desired folder (e.g. mount /dev/sdb /storage/ for data partition) 
3. find UUID using `sudo blkid`
4. add in fstab using the format `UUID=5e524872-fb2d-4b28-ba23-ca7290ba00fd /home           ext4    defaults        0       0`

# Best practices for HTTP GET endpoint: path or query parameters?

Short answer: things that represent an object or resource got to the path (btw I think you can't chain two path parameters in fast api!). For things that are going to change, use query parameters. source [here](https://stackoverflow.com/questions/30967822/when-do-i-use-path-params-vs-query-params-in-a-restful-api)

# when you git commit to main (or master) instead of your working branch

Use patches!

1. run git log to find the changes you want to undo (for example)
```
commit 97a9560b441f11f496aee74f1247df26349a14cf
Author: Kosmas Palios <kpalios@dialoque3.ilsp.gr>
Date:   Mon Dec 20 18:31:53 2021 +0200

    added handling of jpg response

commit b3ee32310dfb585aeae60ef8539773f715584d45
Author: Kosmas Palios <kpalios@dialoque3.ilsp.gr>
Date:   Mon Dec 20 16:35:54 2021 +0200

    added mock endpoint for json retrieval from frontend

commit 1414d7896e4157fb80fd895d34d5aa6f37fedc86
Merge: 5751d47 5fa9ded
Author: Kosmas Palios <kpalios@dialoque3.ilsp.gr>
Date:   Tue Dec 7 18:45:24 2021 +0200

    Merge branch 's4a' of https://gitlab.com/ilsp-spmd-all/dialogue/generic-voice-assistant into s4a
```

So let's say you have commited the last two commits on the wrong branch. You simply undo them as follows: 
```
git diff --binary 97a9560b441f11f496aee74f1247df26349a14cf 1414d7896e4157fb80fd895d34d5aa6f37fedc86 > undo.patch
```

the binary flag is used if you have commited binary stuff too.
Next, you can run 
```
git apply --check undo.patch
``` 

To see if anything can go rong and finally run 
```
git apply --check undo.patch
```
Then check the changes with `git status` and run `git add` to stage the changes of the diff and commit them as a way to restore the previous files. Finally, merge master to your working branch and then proceed to apply the previous diff, but in reverse.
```
git apply --reverse undo.patch
```
Finally check again the diff. Revise the changes and commit. 

# How to make a status page

In other words, how to make a:
* dashboard of service uptime
* is-it-up page
* service availability monitor page

This requires two things:

A) A nice html page with the info, e.g. https://ilspservices2.statuspage.io/
B) A backend that actually checks periodically on the endpoints/URL we need to be alive and report it to A

The first part is done by the statuspage, given by atlassian. You want to keep an eye on an endpoint? Define it as a **component** and it will show up 
in the status page. 

The second part can't be so hard either, but I couldnt do it in one take. Firstly, atlassian's statuspage works with emails to report incidents, e.g. to `theano-<largehashvalue>@atlassian.com`. So I would have to create a service that periodically checks the endpoints and reports by email. This is easy, but I have to configure an email client for the bash, like [here](https://www.linuxscrew.com/bash-send-email)

(ps could [this](https://docs.sendgrid.com/for-developers/sending-email/getting-started-smtp help with the conf?))

# Building chatbots with Rasa X : Actions server

Rasa X is supposed to enable people to build their own chatbot without having to write a line of code. While this is technically true, there are many cases where an [actions server](https://rasa.com/docs/rasa/actions/) is necessary. [It's not hard to connect an actions server to Rasa X](https://forum.rasa.com/t/how-to-run-custom-action-server-for-rasa-x/46115/2). However, in order to do so without having to access the Rasa X server you need to set up a couple of things:

1. Write a Dockerfile for your actions server [Dockerfile here](https://gitlab.com/ilsp-spmd-all/public/build-your-own-chatbot-base-g1/-/blob/main/actions/Dockerfile)
2. (skip this step if you're using gitlab) create a gitlab repo and add it as a remote to your local repo [like this](https://articles.assembla.com/en/articles/1136998-how-to-add-a-new-remote-to-your-git-repo)
3. Add a CICD pipeline to the gitlab repo that builds the actions server and stores it to the repository's own gitlab registry. For example, use [this ci-cd file](https://gitlab.com/ilsp-spmd-all/public/build-your-own-chatbot-base-g1/-/blob/main/.gitlab-ci.yml) from [this gitlab repo](https://gitlab.com/ilsp-spmd-all/public/build-your-own-chatbot-base-g1). To test this step, you can push to the gitlab repo and see the job running from the ci/cd pipeline panel. It will not run if there is not Dockerfile in the actions dir, or if it is invalid. If it runs sucessfully, you will see an image pushed in the container registry of the project (found in the "packages and registries" menu on the left panel)

Finally, log into the server hosting rasa-x and:

1. Find the docker compose file of rasa X, and set the `app` service to point to the image hosted at the gitlab repo, e.g. registry.gitlab.com/ilsp-spmd-all/public/build-your-own-chatbot-base-g1:latest  
2. Log in to the container repo using a personal access token of the gitlab repo, using this command: `docker login registry.example.com -u <username> -p <token>`
3. Test that the app service is being pulled, by running docker-compose pull app
4. Automate the pull and restart process using a dockerized [watchtower](https://containrrr.dev/watchtower/usage-overview/) service as follows:

```
docker run -d \
  --name watchtower \
  -v /home/<user>/.docker/config.json:/config.json \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower registry.gitlab.com/ilsp-spmd-all/public/build-your-own-chatbot-base-g1:latest --debug --interval 60s
  ```
where you replace the `registry.gitlab.com/ilsp-spmd-all/public/build-your-own-chatbot-base-g1` image with your own. You may set the interval value to the polling frequency.

# How to quickly make a tutorial with terminal commands, avoiding the screencast solution

You can use the script and scriptreplay commands. Add this line to your .${SHELL}rc file:
```
alias rec='c=$(date "+%d.%m.%Y_%H.%M") && script -t/home/$USER/session_recs/script_$c_time.log -a /home/$USER/session_recs/script_$c.log'
```

Now when you can type `rec` on the terminal, run some commands, and type `exit`, this will create a pair of files in the `session_recs` folder, a commands log and time log. These
can be used to playback the session, as follows:
```
scriptreplay -t <time_log> <commands_log>
```

If you don't want to use live replay, you can just `cat` the command log.

# How to quickly make a tutorial with terminal commands pt2: making a rec function
Now just add this function to your bashrc

```
rec () {
  c=$(date "+%d.%m.%Y_%H.%M")
  if [ -z "$1" ]; then
    echo "Recording in the session_recordings dir"
    script -t/home/$USER/session_recordings/script_${c}_time.log -a /home/$USER/session_recordings/script_${c}.log
  else
    echo "Recording in the session_recordings/$1 dir"
    mkdir -p /home/$USER/session_recordings/$1
    script -t/home/$USER/session_recordings/$1/script_${c}_time.log -a /home/$USER/session_recordings/$1/script_${c}.log
  fi
}
```

# How to quickly make a tutorial with terminal commands pt3: adding a replay function
```
replay () {
  # takes dir as first argument
  # dir must be the dir filled by rec
  # and possibly edited by script_time_shortener.py
  directory= $1
  speed=$2
  ls $1
  if [ -z $1 ]; then
    echo "no folder given"
    return 1
  else
    files=`ls $1/*no_delays`
    if [ -z $files ]; then
      echo "there is no time-reduced time file, proceedign with the normal one"
      scriptreplay -t $1/script_*time* $1/script_*?[0-9].log $speed
    else
      scriptreplay -t $1/*no_delays $1/script_*?[0-9].log $speed
    fi
  fi
}
```

# What is npm, webpack, babel and what is their relation with react?

check what is installed in the current folder:
```
npm list
```
check this: https://medium.com/@chrislewisdev/react-without-npm-babel-or-webpack-1e9a6049714

# tmux detach connected user

(credits to [dimastro](https://github.com/dimastro))

You can actually detach other people from a tmux session, with `<prefix> D`. The list that opens up shows all connected clients, and the one you choose is detached. 
Don't worry if you work on your own - [someone said it's fun to detach yourself too](https://superuser.com/questions/610608/detach-the-other-tmux-clients#comment755816_610682).

# using pybind to expose C++ functions to python code

1. You need to compile the C++ code using cmake-make
2. Run built C++ executable to ensure it works
3. Write C++ function that uses the pybind C++ lib, as the following example
```
pybind11::bytes
  greeklish2greek(char *input)
  {
      void *cpsz = greeklish_convert(input);
      const char *converted = greeklish_get_text(cpsz);
      char out[2048] = { "\0" };
      strcpy(out, (char *)converted);
      greeklish_release_handle(cpsz);
      return pybind11::bytes(out);
  }
```
4. Define the python module in the same c++ file. This section is extended as you expose more methods of the same lib
```
PYBIND11_MODULE(ag2m, m)
  {
      m.doc() = "Greeklish to greek conversion bindings";
  
      m.def("greeklish2greek", &greeklish2greek, "Convert a string in greeklish to greek");
      m.def("greek2greeklish", &greek2greeklish, "Convert a string in greek to greeklish");
      m.def("init", &init, "Initialize greeklish to greek converter");
      m.def("finish", &finish, "finalize greeklish to greek converter");
  }
```
5. Make a setup.py like [this one](setup_py_example_for_pybind.py) for your "external" module, which uses the new pybind

6. Add an 'API' class to your external module, as follows:
```
import ag2m
class GreeklishConverter(object):
      def __init__(self):
          ag2m.init()
  
      def __del__(self):
          ag2m.finish()
      def grl2g(self, greeklish):
          return ag2m.greeklish2greek(greeklish).decode("iso-8859-7")
```
7. Import said class in the `__init__.py` of your module
8. pip install the shit out if it and you can use it now!

# Autocomplete vim (default in vim >8)
Try these keys:

1. ctrl-n
2. ctrl-p

# When you are running vim and you want to :q but you :Q instead

Try adding these lines in your `.vimrc` file:
```
fun! SetupCommandAlias(from, to)
  exec 'cnoreabbrev <expr> '.a:from
        \ .' ((getcmdtype() is# ":" && getcmdline() is# "'.a:from.'")'
        \ .'? ("'.a:to.'") : ("'.a:from.'"))'
endfun
call SetupCommandAlias("Q","q")
call SetupCommandAlias("W","w")
call SetupCommandAlias("Wq","wq")
call SetupCommandAlias("sp","set paste")

```
The first 5 lines define a function that sets command aliases.
Then we use the function to set aliases at will, and save these precious seconds of your life 
for something better :)

source: https://stackoverflow.com/questions/3878692/how-to-create-an-alias-for-a-command-in-vim



# Next up

* gunicorn, and sockets, and file ownerships. Also, DNS stuff (from first meeting with Manos and the rest of the team)
* using tiny proxy: [easy as f***](https://www.justinmccandless.com/post/set-up-tinyproxy-in-ubuntu/)
* capcha problems, and incapsula weirdness from eody's website
* compose file: images with same name
* set up redshift: https://askubuntu.com/questions/630008/redshift-no-adjustment-method-randr
* auto_up=false in docker
* git fsck utility 
* `.xprofile` tricks
* node bind() (which `this` is this?)
* npm ws vs websocket
* hackernoon/codepen
* https on node.js
* how to juggle with multiple dockerfiles in docker and why do it
* cron jobs, the oldest automation option still in use.
