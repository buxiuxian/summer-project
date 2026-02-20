import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from './HomepageFeatures/Platform-Overview';
// import { UserAuthProvider } from '../components/UserAuthContext';
// import CustomNavbar from '../components/CustomNavbar';
import { translate } from '@docusaurus/Translate';

import Heading from '@theme/Heading';
import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <div 
    style={{ backgroundImage: "url('https://www.geospatialworld.net/wp-content/uploads/2023/07/Remote-Sensing-Analysis-1600x840-1.png')" ,
    // backgroundRepeat: 'no-repeat',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    height:'75vh',
    opacity: 0.8}}>
      <header className={clsx( styles.heroBanner)}>
        <div style={{color: 'dark',opacity: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', height: '50vh'}} >
          <Heading as="h1" className={styles.heroTitle}>
             {translate({id: 'homepage.siteTitle', message: 'Remote Sensing Hub'})}
             </Heading>
             <p className={styles.heroSubtitle}>{translate({id: 'homepage.siteTagline', message: 'Remote Sensing Hub is a shared cloud computing platform for the remote sensing community to compute microwave scattering'})}</p>
        </div>     
      </header>
    </div>

  );
}

export default function Home() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={` ${translate({id: 'homepage.siteTitle', message: 'Remote Sensing Hub'})}`}
      description="Description will go into a meta tag in <head />">
      {/* <CustomNavbar /> */}
      <HomepageHeader />
      <main >
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
