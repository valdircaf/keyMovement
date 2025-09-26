# Extensão Seta - Movimento com Teclado e Mouse

## Descrição
Esta extensão permite controlar o movimento do avatar no Habbo usando:
- **Setas do teclado**: Para movimento preciso a partir da posição atual
- **Cliques do mouse**: Para definir nova posição no quarto

## Pré-requisitos
1. **Python 3.7+** instalado
2. **G-Python** instalado (`pip install g-python`)
3. **pynput** instalado (`pip install pynput`)

## Instalação no G-Earth

### Método 1: Instalação Manual
1. Copie todos os arquivos desta pasta para uma pasta de extensões do G-Earth
2. No G-Earth, vá em **Extensions** → **Install Extension**
3. Selecione o arquivo `extension.json`
4. A extensão aparecerá na lista de extensões disponíveis

### Método 2: Execução Direta
1. Abra o G-Earth
2. Vá em **Extensions** → **Add Extension**
3. Configure:
   - **Title**: Seta - Movimento com Teclado e Mouse
   - **Author**: Valdir
   - **Description**: Use as setas do teclado para mover o avatar
   - **File**: Selecione `key_movement.py`
   - **Arguments**: `--port {port}`

## Como Usar

1. **Inicie o G-Earth** e conecte ao Habbo
2. **Ative a extensão** na lista de extensões
3. **Entre em um quarto** no Habbo
4. **Aguarde** a detecção das dimensões do quarto
5. **Use as funcionalidades**:
   - **Setas do teclado**: ↑↓←→ para mover o avatar
   - **Clique do mouse**: Clique no quarto para ir para uma posição específica
   - **ESC**: Para sair da extensão

## Funcionalidades

- ✅ **Movimento com setas**: Movimento preciso célula por célula
- ✅ **Clique para mover**: Clique em qualquer lugar do quarto
- ✅ **Detecção automática**: Detecta dimensões do quarto automaticamente
- ✅ **Sincronização perfeita**: Mantém posição sincronizada com o servidor
- ✅ **Validação de limites**: Impede movimentos fora do quarto

## Logs de Debug
A extensão mostra informações úteis no console:
- `🎯 POSIÇÃO CAPTURADA`: Quando intercepta movimento do avatar
- `✓ Quarto detectado`: Quando detecta as dimensões do quarto
- `✗ Movimento bloqueado`: Quando tenta mover fora dos limites

## Solução de Problemas

### Extensão não aparece no G-Earth
- Verifique se o arquivo `extension.json` está na pasta correta
- Certifique-se de que o Python está no PATH do sistema

### Setas não funcionam
- Verifique se o `pynput` está instalado: `pip install pynput`
- Execute o G-Earth como administrador se necessário

### Avatar não se move
- Aguarde a detecção das dimensões do quarto
- Verifique se está conectado ao Habbo corretamente
- Veja os logs no console para diagnóstico

## Arquivos da Extensão
- `key_movement.py`: Código principal da extensão
- `extension.json`: Metadados para o G-Earth
- `run_extension.bat`: Launcher para Windows
- `README_EXTENSAO.md`: Este arquivo de instruções