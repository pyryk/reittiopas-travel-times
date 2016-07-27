const _ = require('lodash');
const fs = require('fs');
const path = require('path');

const [, , ...filenames] = process.argv;
const files = filenames.map(f => ({name: path.parse(f).name, file: loadJSON('./' + f)}));

function loadJSON(filename) {
  return JSON.parse(fs.readFileSync(filename, 'utf8'));
}

function prefixFeatureProperties(prefix, feature) {
  const cloned = _.clone(feature);
  cloned.properties = _.mapKeys(cloned.properties, (value, key) => `${prefix}_${key}`);
  return cloned;
}

function combine(files) {
  const groupedFeatures = _(files)
    .map(f => f.file.features.map(feature => prefixFeatureProperties(f.name, feature)))
    .flatten()
    .groupBy(feature => {
      return feature.geometry.coordinates.toString()
    })
    .valueOf();

  const combinedFeatures = _(groupedFeatures)
    .values()
    .map(featureSet => {
      const base = _.cloneDeep(featureSet[0]);
      _.assign(base.properties, ..._.tail(featureSet).map(f => f.properties));

      return base;
    })
    .valueOf();

  return JSON.stringify(_.assign({}, files[0].file, {features: combinedFeatures}), null, 4);
}

console.log(combine(files));
