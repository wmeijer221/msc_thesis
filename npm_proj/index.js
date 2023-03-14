const ChangesStream = require('changes-stream');
const Request = require('request');
const fs = require('fs');
const { stdout } = require('process');


const db = 'https://replicate.npmjs.com';
const output_file_prefix = "./data/npm/"
const output_file_suffix = ".json"

var changes = new ChangesStream({
  db: db,
  include_docs: true
});

console.log("Starting to collect NPM packages.")

start_time = Date.now()
total_processed = 0
total_stored = 0

// Gets data from NPM using a changes stream.
Request.get(db, function (err, req, body) {
  var end_sequence = JSON.parse(body).update_seq;
  changes.on('data', function (change) {
    total_processed += 1
    if (change.seq >= end_sequence) {
      console.log("Done!")
      process.exit(0);
    }

    HandleChange(change)
    LogProgress()
  });
});

function HandleChange(change) {
  if (change.doc) {
    // If a valid entry is received 
    // it's parsed and stored.
    try {
      entry = BuildEntry(change.doc)
      if (IsValidEntry(entry)) {
        StoreEntry(entry)
        total_stored += 1
      }
    }
    catch (e) {
      console.log(e)
      console.log(change.doc)
    }
  }
}

function BuildEntry(doc) {
  if (!doc.versions)
    return undefined

  entry = {
    id: doc._id,
    versions: []
  }

  // Gathers general repository details.
  if (doc.repository) {
    entry.repo = doc.repository.url
  }

  // Gathers details for the different package versions.
  for (const [semver, details] of Object.entries(doc.versions)) {
    version_entry = {
      v: semver,
      lic: details.license,
      deps: details.dependencies,
      devDeps: details.devDependencies
    }

    // Gathers repo details of version
    // if they're different from the main repo.
    if (details.repository
      && details.repository.url !== entry.repo) {
      version_entry.repo = details.repository.url
    }

    entry.versions.push(version_entry)
  }

  return entry
}

function IsValidEntry(entry) {
  if (entry === undefined)
    return false

  has_main_url = entry.repo !== undefined
  has_version_url = entry.versions
    .find(e => e.repo !== undefined) !== undefined

  return has_main_url || has_version_url
}

function StoreEntry(entry) {
  // Builds filename and replaces illegal characters with _.
  safe_entry_id = entry['id'].replace(/[/\\?%*:|"<>\/\@]/g, '_')
  out_path = output_file_prefix + entry['id'] + output_file_suffix
  // Stores json object.
  json_entry = JSON.stringify(entry) + "\n"
  fs.writeFile(out_path, json_entry, err => {
    if (err) {
      console.error(err)
    }
  })
}

function LogProgress() {
  // Writes progress update in console.
  if (total_processed % 5 === 0) {
    stdout.clearLine(0)
    stdout.cursorTo(0)
    cur_time = Date.now()
    dtime = cur_time - start_time
    str_dtime = new Date(dtime)
      .toISOString().slice(11, 19)   // HH:MM:SS
    p_per_sec = Math.floor((total_processed / Math.floor((dtime / 1000)) * 100)) / 100;
    stdout.write(`Processed ${total_processed} packages (${p_per_sec}/s) and of which ${total_stored} were relevant (${str_dtime}).`)
  }
}
