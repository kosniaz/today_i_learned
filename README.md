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


# Next up


* UNIX TCP sockets
* git fsck utility 
* `.xprofile` tricks

