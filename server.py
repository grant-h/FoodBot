import json
from slack import Slack
from threading import Lock, Timer


class SlackPost():

    def __init__(self, text=""):
        self.text = text
        self.attachments = []

    def addAttachment(self, title, content, color, fallback, extra={}):
        attachment = {"color": color, "pretext": title,
                                 "fallback": fallback, "text": content,
                                 "mrkdwn_in": ["text", "pretext"]}
        attachment.update(extra)

        self.attachments.append(attachment)

    def merge(self, other):
        if self.text == "":
            self.text = other.text
        elif other.text != "":
            self.text = "\n".join([self.text, other.text])

        self.attachments += other.attachments

    def render(self):
        return {"text": self.text, "attachments": self.attachments}

    def __str__(self):
        return json.dumps(self.render())


class SlackServer():

    def __init__(self, url, name, username, channel, admin, batch, testing=False):
        self.slack = Slack(url)
        self.name = name
        self.username = username
        self.channel = channel
        self.batchTime = batch[0]
        self.batchAmount = batch[1]
        self.postLock = Lock()
        self.testing = testing
        self.admin = admin

        self.batchEnabled = self.batchAmount > 0
        self.usingTimer = self.batchTime > 0

        self.posts = []

    def post(self, content):
        with self.postLock:
            self.posts.append(SlackPost(content))

            if not self.batchEnabled or len(self.posts) >= self.batchAmount:
                self._flush()
            elif self.usingTimer and len(self.posts) == 1:  # start timer
                self.timer = Timer(self.batchTime, self.flush)
                self.timer.daemon = True
                self.timer.start()

    def postRich(self, title, content, color, fallback, extra={}):
        post = SlackPost()
        post.addAttachment(title, content, color, fallback, extra)

        with self.postLock:
            self.posts.append(post)

            if not self.batchEnabled or len(self.posts) >= self.batchAmount:
                self._flush()
            elif self.usingTimer and len(self.posts) == 1:  # start timer
                self.timer = Timer(self.batchTime, self.flush)
                self.timer.daemon = True
                self.timer.start()

    def flush(self):
        with self.postLock:
            if self.timer is not None:  # cancel any outstanding timers
                self.timer.cancel()

            if len(self.posts) > 0:
                self._flush()

    def _flush(self):
        final_post = SlackPost()

        for i in self.posts:
            final_post.merge(i)

        data = final_post.render()

        if self.testing:
            data.update({"channel": self.admin, "username": self.username})
        else:
            data.update({"channel": self.channel, "username": self.username})

        # print "Sending: " + str(data)
        import urllib2

        try:
            self.slack.send(data)

            # clear posts
            self.posts = []
        except urllib2.HTTPError as e:
            print("EXCEPTION: " + str(e))

    def __str__(self):
        if self.batchTime:
            return u"<SlackServer {}, username {}, channel {}, batch [time {}, amount {}]>".format(
                self.name, self.username, self.channel, self.batchTime, self.batchAmount)
        else:
            return u"<SlackServer {}, username {}, channel {}>".format(
                self.name, self.username, self.channel)
