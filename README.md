This program is used for sending posts to twitter. It is being
specialized for sending notification of svn/trac changes.

To use this you need to install `simplejson` and `oauth2` which are
both available `easy_install` or through many of the standard package managers.

SVN
===
To use the svn mode add the following (or something like it) to your 
post-commit:

> TWIT_HOOK="/usr/local/bin/CodeNotifier.py"
> "$TWIT_HOOK" --config /home/svn/CodeNotifier_config.py svn "$REPOS" "$REV"

This will do nothing if it thinks the trac hook will fire.

TRAC
====
The trac mode is a bit harder to configure, but here are the tips to making 
it work.

1. Add a line to `/etc/aliases`

> twit_trac_submit: "|/usr/local/bin/twit_trac.sh"

2. Add that email address to your `smtp_always_cc` in your `conf/trac.ini` as 
something like `twit_trac_submit@mymachinename.net`.

3. Create a file `/usr/local/bin/twit_trac.sh` with the contents:

> #!/bin/sh
> cat - | /usr/local/bin/CodeNotifier.py --config /usr/local/bin/CodeNotifier_config.py trac
