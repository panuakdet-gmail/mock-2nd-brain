# Password-protected publishing

Only when the user asks.

## Before anything is uploaded

1. Confirm the request in this session. A yes from an earlier session does not count.
2. Say in one sentence what goes up (the `html/` folder: the wiki pages only, no source files) and where (Vercel, behind one shared username and password), then wait for a yes.
3. Check `vercel whoami`. If not logged in, ask the user to type `! vercel login`, since the login is interactive.

## How the gate works

`assets/deploy/middleware.js` runs before every request. It demands HTTP Basic credentials and compares them with two environment variables, `SITE_USER` (defaults to `team`) and `SITE_PASSWORD`. If the password variable is missing, or anything fails, it refuses the request, so a mistake in setup leaves the site locked and never open. `vercel.json` adds no-index, no-referrer and no-cache headers to every response.

One username and password are shared by everyone the user gives them to. Changing the password means changing the variable and deploying again.

## Steps

1. Create `deploy/` at the vault root and copy the assets in: `middleware.js` and `vercel.json` as they are, `gitignore` as `.gitignore`, `vercelignore` as `.vercelignore`, and `package.json` with its `name` set to a neutral project name that does not reveal the document's subject.
2. Copy the built site into `deploy/public/`. Copy `html/` only. Never the vault root, `raw/`, or any source file.
3. Make a password of four random words and a number. Do not reuse one.
4. From inside `deploy/`:

   ```bash
   vercel link --yes --project <neutral-name>
   printf '%s' '<password>' | vercel env add SITE_PASSWORD production
   printf '%s' '<username>' | vercel env add SITE_USER production
   vercel deploy --prod --yes
   ```

   If `vercel link` says the project does not exist, run `vercel project add <neutral-name>` and link again. Run every `vercel` command from inside `deploy/`. Run from the vault root, it uploads the source documents.

5. Verify with `curl -s -o /dev/null -w '%{http_code}'` against the home page and one inner page, on the production address and on the deployment's own unique address:
   - with no credentials: `401` every time;
   - with a wrong password: `401`;
   - with the right credentials: `200`.

   If any request without the right credentials returns `200`, remove the deployment at once and tell the user.

6. Write the access note at the vault root, in the wiki's language, in a file whose name says it must not be shared. It holds the address, the username, the password, the commands to change the password, and the command that takes the site down:

   ```bash
   cd deploy
   vercel env rm SITE_PASSWORD production --yes
   printf '%s' '<new password>' | vercel env add SITE_PASSWORD production
   vercel deploy --prod --yes
   ```

   ```bash
   cd deploy
   vercel remove <neutral-name> --yes
   ```

7. Tell the user the address, where the access note is, and that the password is in it. Do not print the password in chat unless asked, and never write it into `PROMPT_LOG.md`.

## After the wiki changes

Rebuild the HTML, replace `deploy/public/` with the new `html/`, and run `vercel deploy --prod --yes` from `deploy/`. The password stays the same. This is a new upload, so do it only when the user asks.

## Taking it down

When the user asks, run the remove command and confirm the address no longer responds. It deletes the deployments and leaves an empty project behind; `vercel project rm <neutral-name>` deletes that too. The site stays up until someone removes it; mention this once, when publishing, in the access note.
