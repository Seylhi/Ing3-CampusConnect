// Execute par MongoDB au premier demarrage (volume vide) : cree les bases du data lake.
for (const base of ["raw", "curated"]) {
  for (const collection of ["badges", "capteurs"]) {
    db.getSiblingDB(base).createCollection(collection);
  }
}
