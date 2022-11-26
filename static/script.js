const app = Vue.createApp({
    data() {
        return {
            title: 'The Final Empire',
            register: false,
            registerDetails:{
                name: '',
                username: '',
                email: '',
                password: '',
                surname: '',
            }
        }
    },
    methods: {
        registerUser() {
            call = axios.post('/register', this.registerDetails)
            call.then(response => {
                console.log(response)
            })
        }
    }
})
app.mount('#app')