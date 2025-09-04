// Remplacez cette URL par l'URL de votre backend (obtenue avec ngrok pour les tests locaux)
// Remplacez cette URL par l'URL publique de votre backend hébergé (ex: sur Render, Heroku)
const BASE_URL = 'https://votre-app-django.onrender.com'; // <-- METTEZ VOTRE URL DE PRODUCTION ICI

const CONFIG = {
  API_BASE_URL: BASE_URL,
  TOKEN_PROPERTY_KEY: 'dscc.key'
};

/**
 * Fonction utilitaire pour appeler le backend Django.
 */
function fetchFromDjango(endpoint, options = {}) {
  const baseUrl = CONFIG.API_BASE_URL.replace(/\/+$/, ''); // Remove trailing slashes
  const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'ngrok-skip-browser-warning': 'true'
  };

  // Add Authorization header if token exists
  const token = PropertiesService.getUserProperties().getProperty(CONFIG.TOKEN_PROPERTY_KEY);
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;  // Changed from Token to Bearer
    console.log('Using Authorization header with token');
  } else {
    console.warn('No authentication token found');
  }

  // Merge headers
  const requestOptions = {
    method: options.method || 'GET',
    headers: { ...headers, ...(options.headers || {}) },
    muteHttpExceptions: true
  };

  // Add query parameters for GET requests
  let finalUrl = url;
  if (options.params) {
    const queryString = Object.entries(options.params)
      .filter(([_, value]) => value !== undefined && value !== null)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&');
    
    if (queryString) {
      finalUrl += (url.includes('?') ? '&' : '?') + queryString;
    }
  }

  // Add body for POST/PUT requests
  if (options.data) {
    requestOptions.payload = JSON.stringify(options.data);
  }

  try {
    console.log(`[${requestOptions.method}] ${finalUrl}`);
    console.log('Request Headers:', JSON.stringify(headers, null, 2));
    
    const response = UrlFetchApp.fetch(finalUrl, requestOptions);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    const responseHeaders = response.getAllHeaders();

    console.log(`Response Code: ${responseCode}`);
    
    // Handle non-200 responses
    if (responseCode === 401) {
      console.error('Authentication failed, resetting tokens');
      console.error('Response body:', responseText);
      resetAuth();
      throw new Error('Session expired. Please log in again.');
    } else if (responseCode !== 200) {
      console.error(`API Error (${responseCode}):`, responseText);
      throw new Error(`API request failed with status ${responseCode}: ${responseText}`);
    }

    // Parse JSON response
    try {
      return responseText ? JSON.parse(responseText) : {};
    } catch (e) {
      console.error('Failed to parse JSON response:', e);
      throw new Error('Invalid JSON response from server');
    }
    
  } catch (error) {
    console.error('Error in fetchFromDjango:', error);
    throw new Error(`Failed to fetch data: ${error.message}`);
  }
}

/**
 * Reset authentication by clearing stored tokens
 */
function resetAuth() {
  const props = PropertiesService.getUserProperties();
  props.deleteProperty(CONFIG.TOKEN_PROPERTY_KEY);
  props.deleteProperty(CONFIG.TOKEN_PROPERTY_KEY + '_refresh');
  props.deleteProperty(CONFIG.TOKEN_PROPERTY_KEY + '_user');
  console.log('Authentication reset: Tokens cleared');
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
function getConfig() {
  return {
    configParams: [
      {
        type: 'SELECT_SINGLE',
        name: 'dataType',  // Changé de 'tableName' à 'dataType' pour la cohérence
        displayName: 'Table',
        helpText: 'Sélectionnez la table à afficher',
        options: [
          { label: 'Crashes', value: 'google_play_crashes_overview' },
          { label: 'Installations', value: 'google_play_installs_overview' },
          { label: 'Évaluations', value: 'google_play_ratings_overview' }
        ]
      },
      {
        type: 'TEXT',
        name: 'package_name',
        displayName: 'Package Name',
        helpText: 'Filtrer par nom de package (optionnel)',
        placeholder: 'com.example.app',
        isOptional: true
      },
      {
        type: 'SELECT_SINGLE',
        name: 'date_range_type',
        displayName: 'Période',
        helpText: 'Sélectionnez la période des données',
        options: [
          { label: '7 derniers jours', value: '7days' },
          { label: '30 derniers jours', value: '30days' },
          { label: '90 derniers jours', value: '90days' },
          { label: 'Cette année', value: 'ytd' },
          { label: 'Personnalisée', value: 'custom' }
        ],
        default: '30days'
      },
      {
        type: 'DATE',
        name: 'start_date',
        displayName: 'Date de début',
        helpText: 'Sélectionnez la date de début',
        isDynamic: true,
        isVisible: function(params) {
          return params.date_range_type === 'custom';
        }
      },
      {
        type: 'DATE',
        name: 'end_date',
        displayName: 'Date de fin',
        helpText: 'Sélectionnez la date de fin',
        isDynamic: true,
        isVisible: function(params) {
          return params.date_range_type === 'custom';
        }
      }
    ],
    dateRangeRequired: false
  };
}

/**
 * Récupère le schéma d'une table spécifique depuis l'API
 */
function getSchema(request) {
  const { dataType } = request.configParams;
  const token = PropertiesService.getUserProperties().getProperty(CONFIG.TOKEN_PROPERTY_KEY);
  
  if (!token) {
    throw new Error('Authentification requise. Veuillez vous reconnecter.');
  }
  
  try {
    // Get a sample data row to infer schema
    const response = fetchFromDjango(`/api/looker-connector/${dataType}/`, {
      method: 'GET',
      params: { limit: 1 }  // Just get one row to infer schema
    });

    if (!response || !Array.isArray(response) || response.length === 0) {
      // If no data, return a basic schema with common fields
      console.warn('No data returned from API, using default schema');
      return {
        schema: [
          { name: 'date', dataType: 'STRING', semantics: { conceptType: 'DIMENSION' } },
          { name: 'package_name', dataType: 'STRING', semantics: { conceptType: 'DIMENSION' } },
          { name: 'value', dataType: 'NUMBER', semantics: { conceptType: 'METRIC' } }
        ]
      };
    }

    // Get the first row to infer field types
    const sampleRow = response[0];
    const fields = [];

    // Add fields based on the sample row
    for (const [key, value] of Object.entries(sampleRow)) {
      const field = {
        name: key,
        label: key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
        dataType: typeof value === 'number' ? 'NUMBER' : 'STRING',
        semantics: {
          conceptType: typeof value === 'number' ? 'METRIC' : 'DIMENSION'
        }
      };
      
      // Special handling for date fields
      if (key.includes('date') || key.includes('time') || key === 'day') {
        field.dataType = 'STRING';
        field.semantics.conceptType = 'DIMENSION';
        field.semantics.semanticType = 'YEAR_MONTH_DAY';
      }
      
      fields.push(field);
    }

    return { schema: fields };
    
  } catch (error) {
    console.error('Erreur lors de la récupération du schéma:', error);
    // Return a basic schema as fallback
    return {
      schema: [
        { name: 'date', dataType: 'STRING', semantics: { conceptType: 'DIMENSION' } },
        { name: 'package_name', dataType: 'STRING', semantics: { conceptType: 'DIMENSION' } },
        { name: 'value', dataType: 'NUMBER', semantics: { conceptType: 'METRIC' } }
      ]
    };
  }
}

/**
 * Récupère les données d'une table spécifique depuis l'API
 */
function getData(request) {
  const { dataType } = request.configParams;
  const token = PropertiesService.getUserProperties().getProperty(CONFIG.TOKEN_PROPERTY_KEY);
  
  if (!token) {
    throw new Error('Authentication required. Please log in again.');
  }

  // Get date range parameters
  const startDate = request.configParams.start_date || '';
  const endDate = request.configParams.end_date || '';
  const packageName = request.configParams.package_name || '';

  try {
    // Build query parameters
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (packageName) params.package_name = packageName;

    // Get the data from the API
    const response = fetchFromDjango(`/api/looker-connector/${dataType}/`, {
      method: 'GET',
      params: params
    });

    // If response is not an array, wrap it in an array
    const data = Array.isArray(response) ? response : [response];
    
    // Get the schema for the fields
    const schema = getSchema(request).schema;
    
    // Map the data to the expected format
    const rows = data.map(item => {
      const row = [];
      schema.forEach(field => {
        // Handle nested fields if needed
        const value = field.name.split('.').reduce((obj, key) => 
          (obj && obj[key] !== undefined) ? obj[key] : null, 
          item
        );
        row.push(value);
      });
      return { values: row };
    });

    return {
      schema: schema,
      rows: rows
    };

  } catch (error) {
    console.error('Error fetching data:', error);
    throw new Error(`Failed to fetch data: ${error.message}`);
  }
}

/**
 * Helper function to get the correct endpoint for each table
 */
function getEndpointForTable(tableName) {
  // Map the table names to their corresponding API endpoints
  const tableMap = {
    'google_play_installs_overview': 'installs',
    'google_play_ratings_overview': 'ratings',
    'google_play_crashes_overview': 'crashes',
    'installs': 'installs',
    'ratings': 'ratings',
    'crashes': 'crashes'
  };

  const endpoint = tableMap[tableName];
  if (!endpoint) {
    throw new Error(`Unsupported table: ${tableName}. Supported tables are: ${Object.keys(tableMap).join(', ')}`);
  }

  return `/api/looker-connector/${endpoint}/`;
}

/**
 * Fonction utilitaire pour mapper les types de champs
 */
function mapFieldType(dbType) {
  if (!dbType) return 'STRING';
  
  const typeMap = {
    'int4': 'NUMBER',
    'int8': 'NUMBER',
    'numeric': 'NUMBER',
    'float8': 'NUMBER',
    'bool': 'BOOLEAN',
    'date': 'DATE',
    'timestamp': 'DATETIME',
    'timestamptz': 'DATETIME',
    'varchar': 'STRING',
    'text': 'STRING',
    'jsonb': 'STRING'
  };
  
  return typeMap[dbType.toLowerCase()] || 'STRING';
}

function setCredentials(request) {
  // Vérification de la présence de request et request.userPass
  if (!request || !request.userPass) {
    console.error('Requête ou informations de connexion manquantes');
    return {
      errorCode: 'INVALID_CREDENTIALS',
      message: 'Les informations de connexion sont manquantes'
    };
  }

  const { username, password } = request.userPass || {};
  
  if (!username || !password) {
    console.error('Email ou mot de passe manquant');
    return {
      errorCode: 'INVALID_CREDENTIALS',
      message: 'L\'email et le mot de passe sont requis'
    };
  }

  try {
    // Update this URL to match your actual authentication endpoint
    const authUrl = CONFIG.API_BASE_URL + '/client/login/';
    console.log('URL d\'authentification:', authUrl);

    const response = UrlFetchApp.fetch(authUrl, {
      method: 'POST',
      contentType: 'application/json',
      payload: JSON.stringify({
        email: username,
        password: password
      }),
      muteHttpExceptions: true
    });

    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    console.log('Réponse d\'authentification:', { code: responseCode, body: responseText });

    if (responseCode === 200) {
      const data = JSON.parse(responseText);
      if (data && data.access) {
        // Store the token with the correct property key
        PropertiesService.getUserProperties()
          .setProperty(CONFIG.TOKEN_PROPERTY_KEY, data.access);
        
        // Store refresh token if available
        if (data.refresh) {
          PropertiesService.getUserProperties()
            .setProperty(CONFIG.TOKEN_PROPERTY_KEY + '_refresh', data.refresh);
        }
        
        // Store user info if available
        if (data.user) {
          PropertiesService.getUserProperties()
            .setProperty(CONFIG.TOKEN_PROPERTY_KEY + '_user', JSON.stringify(data.user));
        }
        
        console.log('✅ Authentification réussie, token enregistré');
        console.log('Token:', data.access.substring(0, 10) + '...'); // Log first 10 chars of token
        return { errorCode: 'NONE' };
      } else {
        console.error('Token non reçu dans la réponse:', data);
      }
    }
    
    // Handle authentication errors
    let errorMessage = 'Échec de l\'authentification';
    try {
      const errorData = JSON.parse(responseText);
      if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      } else if (errorData.error) {
        errorMessage = errorData.error;
      }
    } catch (e) {
      console.error('Erreur lors de l\'analyse de la réponse d\'erreur:', e);
      errorMessage = `Erreur serveur (${responseCode}): ${responseText.substring(0, 100)}...`;
    }
    
    console.error('Échec de l\'authentification. Détails:', errorMessage);
    return { 
      errorCode: 'INVALID_CREDENTIALS',
      message: errorMessage
    };
    
  } catch (e) {
    console.error('Erreur d\'authentification:', e);
    return { 
      errorCode: 'INVALID_CREDENTIALS', 
      message: 'Échec de l\'authentification: ' + (e.message || 'Erreur inconnue')
    };
  }
}

/**
 * Test function to verify connection and data retrieval
 */
function testConnection() {
  try {
    console.log('=== Début du test de connexion ===');
    
    // 1. Tester l'authentification
    console.log('\n1. Test d\'authentification...');
    const testCredentials = {
      userPass: {
        username: 'imed@clubprivileges.app',
        password: 'imed2025*'
      }
    };
    
    const authResult = setCredentials(testCredentials);
    if (authResult.errorCode === 'NONE') {
      console.log('✅ Authentification réussie');
    } else {
      console.error('❌ Échec de l\'authentification:', authResult.message);
      return;
    }
    
    // 2. Tester la récupération des données avec différentes périodes
    const testPeriods = [
      { 
        label: 'Période personnalisée', 
        value: 'custom', 
        start: '2023-03-13',  
        end: '2023-03-13'     
      }
    ];
    
    for (const period of testPeriods) {
      console.log(`\nTest avec la période: ${period.label}`);
      
      try {
        const dataRequest = {
          configParams: {
            dataType: 'google_play_ratings_overview',
            package_name: 'com.purpi',
            date_range_type: period.value,
            start_date: period.start,
            end_date: period.end
          }
        };
        
        const data = getData(dataRequest);
        console.log(`✅ Données récupérées avec succès pour ${period.label}`);
        console.log('Schéma des données:', data.schema);
        console.log('Nombre d\'enregistrements:', data.rows.length);
        if (data.rows.length > 0) {
          console.log('Exemple de données:', data.rows[0]);
        }
        
      } catch (e) {
        console.error(`❌ Erreur avec la période ${period.label}:`, e.message);
      }
    }
    
    console.log('\n=== Test de connexion terminé ===');
    return '✅ All tests completed successfully';
    
  } catch (error) {
    console.error('❌ Connection Test Failed:', error);
    throw error;
  }
}

// Helper function to clear stored credentials for testing
function clearTestCredentials() {
  const props = PropertiesService.getUserProperties();
  props.deleteProperty(CONFIG.TOKEN_PROPERTY_KEY);
  props.deleteProperty(CONFIG.TOKEN_PROPERTY_KEY + '_refresh');
  props.deleteProperty(CONFIG.TOKEN_PROPERTY_KEY + '_user');
  console.log('Test credentials cleared');
  return 'Test credentials cleared';
}
