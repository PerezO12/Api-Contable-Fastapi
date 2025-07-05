"""
Servicio de traducción usando Transformers para detectar idioma y traducir
"""
from typing import Optional, Tuple, Union, Any
from langdetect import detect, DetectorFactory
import logging

# Configurar seed para reproducibilidad en langdetect
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

# Try to import transformers components
try:
    from transformers.pipelines import pipeline
    from transformers.pipelines.base import Pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
    PipelineType = Pipeline
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("⚠️ Transformers no está disponible. Solo se usará detección de idioma.")
    # Define dummy types for when transformers is not available
    PipelineType = Any
    pipeline = None
    torch = None

# Try to import sentencepiece (opcional, T5 tiene su propio tokenizer integrado)


class TranslationService:
    """Servicio singleton para manejo de traducción"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Pipelines de traducción (inicializar como None)
            self.es_to_en_pipeline: Optional[Any] = None
            self.pt_to_en_pipeline: Optional[Any] = None
            self.en_to_es_pipeline: Optional[Any] = None
            self.en_to_pt_pipeline: Optional[Any] = None
            
            # Flag para indicar si los pipelines están disponibles
            self.pipelines_loaded = False
            
            # No cargar pipelines automáticamente para evitar bloquear el inicio
            # Se cargarán bajo demanda (lazy loading)
            logger.info("🔄 TranslationService inicializado. Los modelos se cargarán bajo demanda.")
            
            TranslationService._initialized = True
    
    def _load_translation_pipelines(self):
        """Carga todos los pipelines de traducción al inicializar"""
        try:
            if not TRANSFORMERS_AVAILABLE or torch is None or pipeline is None:
                logger.warning("⚠️ transformers o torch no están disponibles.")
                return
            
            device = 0 if torch.cuda.is_available() else -1
            
            logger.info("Cargando pipelines de traducción con modelos alternativos...")
            
            # Usar modelos T5 que no requieren sentencepiece
            try:
                logger.info("Intentando cargar modelos T5 para traducción...")
                
                # T5 para español-inglés
                t5_es_en = pipeline(
                    "text2text-generation",
                    model="t5-small",
                    device=device
                )
                self.es_to_en_pipeline = lambda text: [{'translation_text': 
                    t5_es_en(f"translate Spanish to English: {text}")[0]['generated_text']}]
                
                # T5 para inglés-español  
                t5_en_es = pipeline(
                    "text2text-generation", 
                    model="t5-small",
                    device=device
                )
                self.en_to_es_pipeline = lambda text: [{'translation_text':
                    t5_en_es(f"translate English to Spanish: {text}")[0]['generated_text']}]
                
                # Para portugués, usar las mismas instancias con prefijos diferentes
                self.pt_to_en_pipeline = lambda text: [{'translation_text':
                    t5_es_en(f"translate Portuguese to English: {text}")[0]['generated_text']}]
                
                self.en_to_pt_pipeline = lambda text: [{'translation_text':
                    t5_en_es(f"translate English to Portuguese: {text}")[0]['generated_text']}]
                
                logger.info("✅ Pipelines T5 cargados exitosamente")
                self.pipelines_loaded = True
                
            except Exception as t5_error:
                logger.warning(f"⚠️ No se pudieron cargar modelos T5: {t5_error}")
                logger.info("Continuando sin traducción...")
                
                # Fallback: crear pipelines que simplemente devuelven el texto original
                logger.info("🔄 Creando pipelines de fallback (sin traducción)...")
                self.es_to_en_pipeline = lambda text: [{'translation_text': text}]
                self.en_to_es_pipeline = lambda text: [{'translation_text': text}]
                self.pt_to_en_pipeline = lambda text: [{'translation_text': text}]
                self.en_to_pt_pipeline = lambda text: [{'translation_text': text}]
                self.pipelines_loaded = True
                logger.warning("⚠️ Pipelines de fallback activos (solo pasan el texto original)")
            
        except Exception as e:
            logger.warning(f"⚠️ Error cargando pipelines de traducción: {e}")
            logger.warning("El servicio de traducción funcionará con funcionalidad limitada (solo detección de idioma)")
            
            # Último fallback: crear pipelines que simplemente devuelven el texto original
            self.es_to_en_pipeline = lambda text: [{'translation_text': text}]
            self.en_to_es_pipeline = lambda text: [{'translation_text': text}]
            self.pt_to_en_pipeline = lambda text: [{'translation_text': text}]
            self.en_to_pt_pipeline = lambda text: [{'translation_text': text}]
            self.pipelines_loaded = True
    
    def detect_language(self, text: str) -> str:
        """
        Detecta el idioma del texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Código de idioma detectado ('es', 'pt', 'en', 'unknown')
        """
        try:
            if not text.strip():
                return 'unknown'
            
            detected_lang = detect(text)
            
            # Mapear códigos de idioma a los que soportamos
            if detected_lang in ['es', 'ca']:  # español o catalán
                return 'es'
            elif detected_lang in ['pt']:  # portugués
                return 'pt'
            elif detected_lang in ['en']:  # inglés
                return 'en'
            else:
                # Por defecto, asumir español si no se detecta
                logger.warning(f"Idioma no soportado detectado: {detected_lang}, asumiendo español")
                return 'es'
                
        except Exception as e:
            logger.error(f"Error detectando idioma: {e}")
            # En caso de error, asumir español
            return 'es'
    
    def translate_to_english(self, text: str, source_lang: str) -> str:
        """
        Traduce texto al inglés desde el idioma fuente
        
        Args:
            text: Texto a traducir
            source_lang: Idioma fuente ('es', 'pt', 'en')
            
        Returns:
            Texto traducido al inglés
        """
        try:
            if source_lang == 'en':
                return text
            
            # Cargar pipelines si no están cargados
            if not self.pipelines_loaded:
                self._load_translation_pipelines()
                self.pipelines_loaded = True
            
            if source_lang == 'es' and self.es_to_en_pipeline:
                result = self.es_to_en_pipeline(text)
                if isinstance(result, list) and len(result) > 0:
                    return result[0]['translation_text']
            
            elif source_lang == 'pt' and self.pt_to_en_pipeline:
                result = self.pt_to_en_pipeline(text)
                if isinstance(result, list) and len(result) > 0:
                    return result[0]['translation_text']
            
            # Si no hay pipeline disponible o no se ejecutó la traducción
            logger.warning(f"Pipeline no disponible para {source_lang} -> en")
            return text
                
        except Exception as e:
            logger.error(f"Error traduciendo {source_lang} -> en: {e}")
            return text
    
    def translate_from_english(self, text: str, target_lang: str) -> str:
        """
        Traduce texto desde inglés al idioma objetivo
        
        Args:
            text: Texto en inglés a traducir
            target_lang: Idioma objetivo ('es', 'pt', 'en')
            
        Returns:
            Texto traducido al idioma objetivo
        """
        try:
            if target_lang == 'en':
                return text
            
            # Cargar pipelines si no están cargados
            if not self.pipelines_loaded:
                self._load_translation_pipelines()
                self.pipelines_loaded = True
            
            if target_lang == 'es' and self.en_to_es_pipeline:
                result = self.en_to_es_pipeline(text)
                if isinstance(result, list) and len(result) > 0:
                    return result[0]['translation_text']
            
            elif target_lang == 'pt' and self.en_to_pt_pipeline:
                result = self.en_to_pt_pipeline(text)
                if isinstance(result, list) and len(result) > 0:
                    return result[0]['translation_text']
            
            # Si no hay pipeline disponible o no se ejecutó la traducción
            logger.warning(f"Pipeline no disponible para en -> {target_lang}")
            return text
                
        except Exception as e:
            logger.error(f"Error traduciendo en -> {target_lang}: {e}")
            return text
    
    def process_text(self, text: str) -> Tuple[str, str, str]:
        """
        Procesa un texto: detecta idioma y traduce al inglés
        
        Args:
            text: Texto a procesar
            
        Returns:
            Tupla (idioma_detectado, texto_original, texto_en_inglés)
        """
        detected_lang = self.detect_language(text)
        english_text = self.translate_to_english(text, detected_lang)
        
        return detected_lang, text, english_text


# Instancia singleton
translation_service = TranslationService()
