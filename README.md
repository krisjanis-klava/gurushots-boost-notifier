# GuruShots Boost Notifier

Get a push notification the moment a free "boost" becomes available on one
of your active GuruShots challenges, instead of having to check the app
yourself every hour.

It runs for free on a schedule using GitHub Actions — no server, no
always-on device required. Each person on the team runs their own private
copy (forked from this repo) with their own GuruShots login and their own
notification channel, so nobody shares credentials.

## How it works

A small Python script logs into GuruShots' web API, checks your active
challenges, and sends a notification via [ntfy.sh](https://ntfy.sh) if any
challenge's boost state is `AVAILABLE`. A GitHub Actions workflow runs that
script every 30 minutes automatically.

## Setup (takes about 5 minutes)

### 1. Fork this repository

Click **Fork** at the top of this page to get your own private-or-public
copy under your GitHub account. (A private fork is fine — GitHub Actions
works the same either way.)

### 2. Pick a notification topic on ntfy.sh

[ntfy.sh](https://ntfy.sh) is a free, no-signup push notification service.
Anyone who knows your "topic" name can send to (and read) it, so pick
something hard to guess, e.g. `yourname-gurushots-7f3k2`.

- Install the **ntfy** app on your phone ([iOS](https://apps.apple.com/app/ntfy/id1625396347) / [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy)), or use the [web app](https://ntfy.sh/app).
- Subscribe to the topic name you picked.

**Alternatives to ntfy.sh:** if you'd rather use something else — a
[Pushover](https://pushover.net) topic, a Discord/Slack webhook, email via
a service like [Resend](https://resend.com), etc. — you only need to edit
the `notify()` function in `gurushots_boost_check.py` to POST to your
service of choice instead. Everything else in this guide stays the same.

### 3. Add your secrets to your fork

In your forked repo on GitHub: **Settings → Secrets and variables →
Actions → New repository secret**. Add these three:

| Secret name          | Value                                      |
|-----------------------|---------------------------------------------|
| `GURUSHOTS_EMAIL`    | Your GuruShots login email                 |
| `GURUSHOTS_PASSWORD` | Your GuruShots password                    |
| `NTFY_TOPIC`         | The topic name you picked in step 2        |

Nothing else needs to change — credentials never get written into the code
or committed to git.

### 4. Enable Actions on your fork

Forks have Actions disabled by default. Go to the **Actions** tab on your
fork and click the button to enable workflows.

### 5. Test it

Still on the **Actions** tab, select **GuruShots boost check** in the left
sidebar, then **Run workflow** to trigger it manually. Check the run's log
— it should print each of your active challenges and their boost state.
If a boost is available, you should get a notification within a few
seconds.

Once that works, you're done — it will now run automatically every 30
minutes on its own.

## Adjusting the schedule

Edit the `cron` line in
[`.github/workflows/gurushots-boost-check.yml`](.github/workflows/gurushots-boost-check.yml).
It uses standard [cron syntax](https://crontab.guru/); GitHub may delay
scheduled runs by a few minutes during high load, which doesn't matter
much for this use case. Running much more often than every 15–30 minutes
isn't recommended — GuruShots may rate-limit or flag frequent automated
logins.

## Privacy and security notes

- Your credentials are stored as encrypted GitHub Actions secrets, only
  readable by workflow runs in your own fork — not visible to anyone else,
  including the maintainer of this repo.
- Nobody else can see your notifications unless they know your exact ntfy
  topic name — keep it private, the same way you'd keep a password
  private.
- This uses GuruShots' undocumented web API (the same one the
  gurushots.com website itself uses), not an official/public API. It could
  break if GuruShots changes their site. If it stops working, check the
  Actions tab for error logs.
- Run this at your own discretion — it automates login to your account
  using your real credentials via a third-party GitHub Action runner.

## Running it locally instead

If you'd rather run the check from your own machine instead of GitHub
Actions:

```bash
pip install curl_cffi
GURUSHOTS_EMAIL=you@example.com GURUSHOTS_PASSWORD=yourpassword NTFY_TOPIC=your-topic python3 gurushots_boost_check.py
```
