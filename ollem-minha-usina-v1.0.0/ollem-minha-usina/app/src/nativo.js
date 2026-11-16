// Recursos do celular (Capacitor). No navegador/prévia, tudo cai num modo simples que não quebra.
// >>> PARA O TI: ver docs/PARA-O-TI.md, item "App nativo" (plugins, Firebase, Face ID, ícone e tela de abertura).
import { Capacitor } from '@capacitor/core'

export const nativo = () => Capacitor.isNativePlatform()
export const plataforma = () => Capacitor.getPlatform() // 'ios' | 'android' | 'web'

const memoria = {}

// Token da sessão. No celular usa o Preferences do Capacitor (guardado no app); trocar por um cofre seguro
// (Keychain/Keystore, ex.: plugin capacitor-secure-storage) é recomendado — ver PARA-O-TI.
export async function guardar(k, v) {
  if (nativo()) { const { Preferences } = await import('@capacitor/preferences'); return Preferences.set({ key: k, value: v }) }
  memoria[k] = v
  try { sessionStorage.setItem('ollem_' + k, v) } catch { /* prévia sem armazenamento */ }
}
export async function ler(k) {
  if (nativo()) { const { Preferences } = await import('@capacitor/preferences'); return (await Preferences.get({ key: k })).value }
  try { return memoria[k] || sessionStorage.getItem('ollem_' + k) } catch { return memoria[k] || null }
}
export async function apagar(k) {
  if (nativo()) { const { Preferences } = await import('@capacitor/preferences'); return Preferences.remove({ key: k }) }
  delete memoria[k]
  try { sessionStorage.removeItem('ollem_' + k) } catch { /* nada */ }
}

// Notificações: pede permissão e devolve o token do aparelho (FCM). No navegador devolve null.
export async function ativarNotificacoes() {
  if (!nativo()) return null
  const { PushNotifications } = await import('@capacitor/push-notifications')
  const p = await PushNotifications.requestPermissions()
  if (p.receive !== 'granted') return null
  return new Promise(resolve => {
    PushNotifications.addListener('registration', t => resolve(t.value))
    PushNotifications.addListener('registrationError', () => resolve(null))
    PushNotifications.register()
  })
}
