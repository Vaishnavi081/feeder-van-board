# Deploying for free

You need two things: somewhere to host static files, and (optionally, for a
real shared multi-device board) a Firestore database. Both are free.

## 1. Host the static files — GitHub Pages (~2 min)

1. Push this folder to a public GitHub repo.
2. Repo Settings → Pages → Source → "Deploy from a branch" → `main` / root.
3. Your board is live at `https://<username>.github.io/<repo>/`.

(Netlify Drop or Vercel's free tier work identically — just drag the folder
in — if you'd rather not use GitHub Pages.)

As-is, with `config.js` left empty, this is already a fully working demo:
every visitor gets their own local board (great for judging the UX flow,
not yet a shared board across phones).

## 2. Add a real shared board — Firebase Firestore (~10 min, free "Spark" plan)

1. Go to the [Firebase console](https://console.firebase.google.com/) →
   "Add project" (no billing account required for Spark).
2. Build → Firestore Database → Create database → **Start in test mode**
   for now (open read/write — fine for a no-login community board; see the
   tightened rules below before you publicize the URL widely).
3. Project settings → General → "Your apps" → add a **Web app** → copy the
   `firebaseConfig` object.
4. Paste those values into `config.js` in this repo, commit, push.
5. That's it — `db.js` detects the config and switches from localStorage to
   Firestore automatically. Every visitor now sees the same board update in
   real time.

### Recommended Firestore rules (tighten before sharing widely)

Test mode's default rules expire after 30 days and are wide open. Replace
them with this shape — still no login required, but it stops a client from
writing arbitrary fields or editing someone else's trip:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /boards/{date}/trips/{tripId} {
      allow read: if true;
      allow create: if request.resource.data.keys().hasOnly(
        ['id','routeId','landmarkId','time','vehicleNumber','note',
         'confirmCount','reportCount','createdAt','lastConfirmedAt','deviceId'])
        && request.resource.data.time is string
        && request.resource.data.routeId is string
        && request.resource.data.landmarkId is string
        && request.resource.data.confirmCount is int
        && request.resource.data.reportCount is int;
      allow update: if request.resource.data.diff(resource.data)
        .affectedKeys().hasOnly(['confirmCount','lastConfirmedAt','reportCount']);
      allow delete: if false;
    }
  }
}
```

This is free at any realistic village-board scale (Spark tier: 50k reads
and 20k writes/day at no cost).
