import { connectDB } from "../../../util/database";
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { MongoDBAdapter } from "@next-auth/mongodb-adapter";

export const authOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        phoneNumber: { label: "Phone Number", type: "text" },
        password: { label: "Password", type: "password" },
      },
      
      async authorize(credentials) {
        let db = (await connectDB).db('test');
        let user = await db.collection('user').findOne({ username: credentials.phoneNumber });

        if (!user) {
          console.log('해당 전화번호는 없음');
          return null;
        }

        if (credentials.password !== user.password) {
          console.log('비밀번호 틀림');
          return null;
        }

        console.log('로그인 성공');
        return user;
      }
    })
  ],

  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60
  },

  callbacks: {
    jwt: async ({ token, user }) => {
      if (user) {
        token.user = {};
        token.user.name = user.name;
        token.user.phoneNumber = user.phoneNumber; 
      }
      return token;
    },

    session: async ({ session, token }) => {
      session.user = token.user;
      return session;
    },

    // 로그인 성공 후 리디렉션을 처리하는 콜백 함수
    async redirect({ url, baseUrl }) {
      // 사용자를 /app/Mains 페이지로 리디렉션합니다.
      return '/Mains';
    },
  },

  adapter: MongoDBAdapter(connectDB),
  secret: 'qwer1234'
};

export default NextAuth(authOptions);
