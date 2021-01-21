# Today I Learned: tutorials/memos/logs

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
2. `:%s/  - \(intent: \._\{-}\)\n  \(- user:\._\{-}\n\._\{-}\)/  \2\r  \1/g`
3. Clean up

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
