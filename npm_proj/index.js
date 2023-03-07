const ChangesStream = require('changes-stream');
const Request = require('request');
const fs = require('fs');
const { stdout } = require('process');


const db = 'https://replicate.npmjs.com';
const output_file = './data/npm_projects.json'

var changes = new ChangesStream({
  db: db,
  include_docs: true
});

function BuildEntry(doc) {
  // Filters unnecessary data from entry.

  if (!doc.versions)
    return undefined

  entry = {
    id: doc._id,
    versions: []
  }

  // Gathers general repository details.
  if (doc.repository) {
    entry.repo_type = doc.repository.type
    entry.repo_url = doc.repository.url
  }

  // Gathers details for the different package versions.
  for (const [semver, details] of Object.entries(doc.versions)) {
    version_entry = {
      version: semver,
      license: details.license,
      dependencies: details.dependencies,
      devDependencies: details.devDependencies
    }

    // Gathers repo details of version.
    if (details.repository) {
      version_entry.repo_type = details.repository.type
      version_entry.repo_url = details.repository.url
    }

    entry.versions.push(version_entry)
  }

  return entry
}

function StoreEntry(entry) {
  // Appends result to file.
  json_entry = JSON.stringify(entry) + "\n"
  fs.appendFile(output_file, json_entry, err => {
    if (err) {
      console.error(err)
    }
  })
}

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
    if (change.doc) {
      // If a valid entry is received 
      // it's parsed and stored.
      try {
        entry = BuildEntry(change.doc)
        if (entry) {
          StoreEntry(entry)
          total_stored += 1
        }
      }
      catch (e) {
        console.log(e)
        console.log(doc)
      }
    }

    // Writes progress update in console.
    if (total_processed % 5 === 0) {
      stdout.clearLine(0)
      stdout.cursorTo(0)
      cur_time = Date.now()
      dtime = cur_time - start_time
      str_dtime = new Date(dtime)
        .toISOString().slice(11, 19)   // HH:MM:SS
      p_per_sec = Math.floor((total_processed / Math.floor((dtime / 1000)) * 100)) / 100;
      stdout.write(`Processed (${total_processed}), Stored (${total_stored}), Time spent (${str_dtime}), ${p_per_sec}/s.`)
    }
  });
});
