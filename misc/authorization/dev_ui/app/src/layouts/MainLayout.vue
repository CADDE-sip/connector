<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title>
          認可機能
        </q-toolbar-title>
        <div class="q-px-md">Login : {{login_name}}</div>
        <div>
          <q-btn outline size="md" style="color: rgb(86, 15, 240);" color="primary" @click="logout()" class="full-width text-white" label="ログアウト" />
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
    >
      <q-list>
        <q-item-label
          header
        >
        </q-item-label>

        <EssentialLink
          v-for="link in essentialLinks"
          :key="link.title"
          v-bind="link"
        />
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script>
import { api } from 'boot/axios'
import { defineComponent, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from '../stores/store'
import EssentialLink from 'components/EssentialLink.vue'

const linksList = [
  {
    title: '認可機能の設定',
    caption: '',
    icon: 'settings',
    link: '#settings'
  },
  {
    title: '認可一覧',
    caption: '',
    icon: 'view_list',
    link: '#list'
  },
  {
    title: '認可登録',
    caption: '',
    icon: 'add',
    link: '#register'
  }
]

export default defineComponent({
  name: 'MainLayout',

  components: {
    EssentialLink
  },

  setup () {
    const router = useRouter()
    const store = useStore()
    const leftDrawerOpen = ref(false)
    let login_name = ref('')

    watch(() => store.cadde_user_id,
      (newVal, oldVal) => {
        login_name.value = newVal ? newVal: '-'
      })

    function logout() {
      let obj = {}
      obj.cadde_user_id = ''
      store.updateLoginInfo(obj)
      api.get('/cadde/api/v4/ui/logout')
        .then((response) => {
          console.log('ログアウトレスポンス', response)
        })
        .catch((err) => {
          console.log('ログアウトエラー', err)
          this.confirmDialog.isDisplay = true
          this.confirmDialog.status = err.response.status + ' ' + err.response.statusText
          this.confirmDialog.message = err.response.data.msg
        })
      router.push({ path: '/' })
    }

    return {
      essentialLinks: linksList,
      leftDrawerOpen,
      login_name,
      logout,
      toggleLeftDrawer () {
        leftDrawerOpen.value = !leftDrawerOpen.value
      }
    }
  }
})
</script>
