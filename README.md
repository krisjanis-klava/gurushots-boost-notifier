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

Once that works, the workflow's built-in schedule will run it
automatically — but read the next section before relying on that alone,
since GitHub's free scheduler is not very reliable on its own.

### 6. Make it actually reliable with an external trigger (recommended)

GitHub Actions' own `schedule` trigger is documented as best-effort: it
gets silently delayed or dropped entirely whenever GitHub's shared
scheduler is under load, with no retry or catch-up. In practice this can
mean gaps of several hours between runs instead of the 30 minutes you
asked for — through no fault of this workflow. An API-triggered run
(`workflow_dispatch`, the same thing "Run workflow" uses) doesn't have
this problem — it runs right away, every time. So the reliable way to get
a real 30-minute cadence is to have a free external cron service call that
API on a timer, instead of depending on GitHub's own scheduler.

1. **Create a Personal Access Token** scoped to just this one repo:
   [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new) →
   under "Repository access" pick **Only select repositories** → choose
   your fork → under "Permissions" set **Actions** to **Read and write**
   (that's the only permission it needs). Generate it and copy the token
   — you won't be able to see it again.
2. **Sign up free at [cron-job.org](https://cron-job.org)** (or any
   similar service — [EasyCron](https://www.easycron.com) works too).
3. **Create a new cron job** with these settings:
   - URL: `https://api.github.com/repos/YOUR-USERNAME/YOUR-FORK-NAME/actions/workflows/gurushots-boost-check.yml/dispatches`
   - Method: `POST`
   - Schedule: every 30 minutes
   - Request headers:
     - `Authorization: Bearer YOUR-PERSONAL-ACCESS-TOKEN`
     - `Accept: application/vnd.github+json`
     - `Content-Type: application/json`
   - Request body: `{"ref":"master"}`
4. Save it, then use the service's "Run now"/"Test" button and check your
   fork's **Actions** tab — a new run triggered by `workflow_dispatch`
   should appear within a few seconds.

**If the test comes back "Not Found":** this is a generic error GitHub's
API returns for more than one cause — check these two first, they cover
the vast majority of cases:
- The **Request method** is actually set to `POST`. Some cron services
  default new jobs to `GET`, and a `GET` to this endpoint also returns
  "Not Found" — easy to miss since it looks identical to a bad URL.
- The token actually has **Actions: Read and write** permission checked.
  GitHub's API returns the same generic 404 (not a permissions error) for
  a private repo when the token can't access it — including when it has
  access to the repo but the wrong permission scope.

You can leave the built-in `schedule:` trigger in the workflow as a free
backup layer (it costs nothing and won't cause duplicate notifications —
the script just checks state, it doesn't track "already notified"), but
the external trigger above is what actually gives you a dependable
30-minute cadence.

**Handle that token like a password.** It's scoped to only this one repo
and only to triggering workflows, so a leak is low-blast-radius, but it's
still being pasted into a third-party site's stored configuration. Revoke
it any time from [github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens)
if you ever stop using the cron service.

## Adjusting the schedule

Edit the `cron` line in
[`.github/workflows/gurushots-boost-check.yml`](.github/workflows/gurushots-boost-check.yml)
if you want to change the built-in backup schedule. It uses standard
[cron syntax](https://crontab.guru/), and runs at `:07`/`:37` rather than
`:00`/`:30` since those are the busiest minutes on GitHub's shared
scheduler and get delayed/dropped the most — but per the section above,
this is a backup, not something to rely on for a precise cadence. Running
much more often than every 15–30 minutes isn't recommended either way —
GuruShots may rate-limit or flag frequent automated logins.

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
