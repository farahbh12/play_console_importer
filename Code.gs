// Remplacez cette URL par l'URL de votre backend (obtenue avec ngrok pour les tests locaux)
// Remplacez cette URL par l'URL publique de votre backend hébergé (ex: sur Render, Heroku)
const BASE_URL = 'https://votre-app-django.onrender.com'; // <-- METTEZ VOTRE URL DE PRODUCTION ICI

/**
 * Fonction utilitaire pour appeler le backend Django.
 */
function fetchFromDjango(endpoint, options) {
  const url = BASE_URL + endpoint;
  const fetchOptions = options || {};
  fetchOptions.muteHttpExceptions = true; // Très important pour le débogage !

    // Ajoute la clé API aux en-têtes si elle existe
  const userProperties = PropertiesService.getUserProperties();
  const apiKey = userProperties.getProperty('dscc.key');
  if (apiKey) {
    fetchOptions.headers = fetchOptions.headers || {};
    fetchOptions.headers['Authorization'] = 'ApiKey ' + apiKey;
  }

  const response = UrlFetchApp.fetch(url, fetchOptions);
  const responseCode = response.getResponseCode();
  const responseBody = response.getContentText();

  if (responseCode >= 400) {
    // Si le backend retourne une erreur (4xx ou 5xx)
        const errorText = 'Le backend a retourné une erreur (Code: ' + responseCode + '). Contactez le support.';
    let debugText = 'URL: ' + url + '\nRéponse du backend: ' + responseBody;
    // Affiche le message d'erreur détaillé uniquement pour les admins
    if (!isAdminUser()) {
        debugText = 'Détails non disponibles. Contactez un administrateur.';
    }
    DataStudioApp.createCommunityConnector().newUserError().setText(errorText).setDebugText(debugText).throwException();
  }

  try {
    return JSON.parse(responseBody);
  } catch (e) {
    // Si la réponse n'est pas du JSON valide
    const errorText = "La réponse du backend n'est pas un JSON valide.";
    const debugText = 'URL: ' + url + '\nRéponse reçue: ' + responseBody;
    DataStudioApp.createCommunityConnector().newUserError().setText(errorText).setDebugText(debugText).throwException();
  }
}

// Fonction requise par Looker Studio
function getAuthType() {
  const cc = DataStudioApp.createCommunityConnector();
  return cc.newAuthTypeResponse()
    .setAuthType(cc.AuthType.KEY)
    .setHelpUrl('https://docs.votreprojet.com/looker-studio-connector#api-key') // Optionnel: URL d'aide
    .build();
}

function isAdminUser() {
  return Session.getEffectiveUser().getEmail().endsWith('@mon-domaine-admin.com'); // Mettez votre domaine admin
}

/**
 * Étape 1: Affiche un menu déroulant avec les tables de la base de données.
 */
function getConfig(request) {
  const cc = DataStudioApp.createCommunityConnector();
  const config = cc.getConfig();

  config.newInfo()
    .setId('instructions')
    .setText('Connecteur personnalisé pour la base de données via Django.');

  // Appel à l'endpoint /looker-studio/tables/
  const tablesResponse = fetchFromDjango('/looker-studio/tables/');
  const tableSelect = config.newSelectSingle()
    .setId('table_name')
    .setName('Sélectionnez une table');

  if (tablesResponse && tablesResponse.tables) {
        tablesResponse.tables.forEach(table => {
      // CORRECTION: Utiliser table.label pour l'affichage et table.name pour la valeur
      tableSelect.addOption(config.newOptionBuilder().setLabel(table.label).setValue(table.name));
    });
  } else {
      tableSelect.addOption(config.newOptionBuilder().setLabel('Aucune table trouvée').setValue(''));
  }
  
  config.setDateRangeRequired(true);

  return config.build();
}

/**
 * Étape 2: Récupère le schéma de la table sélectionnée.
 */
function getSchema(request) {
  const tableName = request.configParams.table_name;
  if (!tableName) {
    return { schema: [] };
  }

  const cc = DataStudioApp.createCommunityConnector();
  const fields = cc.getFields();
  const types = cc.FieldType;
  const aggregations = cc.AggregationType;

  // Mapping des types de données
  const typeMap = {
    'NUMBER': types.NUMBER,
    'TEXT': types.TEXT,
    'BOOLEAN': types.BOOLEAN,
    'YEAR_MONTH_DAY': types.YEAR_MONTH_DAY,
    'YEAR_MONTH_DAY_HOUR': types.YEAR_MONTH_DAY_HOUR,
    'CURRENCY_USD': types.CURRENCY_USD
  };

  // Appel à l'endpoint /looker-studio/tables/{table_name}/schema/
  const schemaResponse = fetchFromDjango(`/looker-studio/tables/${tableName}/schema/`);

  schemaResponse.schema.forEach(fieldInfo => {
    const isMetric = ['NUMBER', 'CURRENCY_USD'].includes(fieldInfo.dataType);
    const field = isMetric ? fields.newMetric() : fields.newDimension();
    
    field.setId(fieldInfo.name);
    field.setName(fieldInfo.label);
    field.setType(typeMap[fieldInfo.dataType] || types.TEXT);
    
    if (isMetric) {
        field.setAggregation(aggregations.SUM);
    }
  });

  return fields.build();
}

/**
 * Étape 3: Récupère les données de la table.
 */
function getData(request) {
  const tableName = request.configParams.table_name;
  const requestedFields = getSchema(request).getFieldsForIds(request.fields.map(field => field.name));

  // Prépare la requête POST pour Django
  const postPayload = {
    fields: requestedFields.map(field => field.getId())
  };

  const postOptions = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(postPayload)
  };

  // Appel à l'endpoint /looker-studio/tables/{table_name}/data/
  const dataResponse = fetchFromDjango(`/looker-studio/tables/${tableName}/data/`, postOptions);

    // CORRECTION: La réponse de Django contient déjà les données formatées dans `rows`
  const data = dataResponse.rows;

  return DataStudioApp.createCommunityConnector().newDataResponse()
    .setFields(requestedFields)
    .addAllRows(data)
    .build();
}
